import io
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from dotenv import load_dotenv
from google import genai
from PyPDF2 import PdfReader
from docx import Document


APP_TITLE = "HR CV Screener"
MODEL = "gemini-2.5-flash"
SYSTEM_PROMPT_PATH = "system_prompt.txt"
DEFAULT_SYSTEM_PROMPT = """You are an expert HR recruitment analyst. You will be given a Job Description and one Candidate CV.

Your task:
1. Analyze how well the CV matches the Job Description.
2. Return ONLY a valid JSON object — no explanation, no markdown, no extra text.

JSON format:
{
  "candidate_name": "Full name from CV or 'Unknown'",
  "match_score": <integer 0-100>,
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2"],
  "summary": "2-3 sentence recruiter summary of this candidate."
}
"""

@dataclass
class CandidateResult:
    filename: str
    candidate_name: str
    match_score: int
    matched_skills: List[str]
    missing_skills: List[str]
    summary: str
    raw: Dict[str, Any]


def load_system_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    parts: List[str] = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        if txt.strip():
            parts.append(txt)
    return "\n\n".join(parts).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    # python-docx expects a file-like object; Streamlit gives bytes.
    doc = Document(io.BytesIO(file_bytes))
    parts = [(p.text or "").strip() for p in doc.paragraphs]
    parts = [p for p in parts if p]
    return "\n".join(parts).strip()


def extract_text(uploaded_file) -> Tuple[str, str]:
    name = uploaded_file.name
    suffix = os.path.splitext(name)[1].lower()
    data = uploaded_file.getvalue()

    if suffix == ".pdf":
        return name, extract_text_from_pdf(data)
    if suffix == ".docx":
        return name, extract_text_from_docx(data)
    raise ValueError(f"Unsupported file type: {suffix}")


def clamp_int(value: Any, lo: int, hi: int, default: int) -> int:
    try:
        n = int(value)
    except Exception:
        return default
    return max(lo, min(hi, n))


def parse_model_json(content: str) -> Dict[str, Any]:
    # Best-effort: model should return JSON object only; still guard against stray whitespace.
    content = content.strip()
    try:
        obj = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        obj = json.loads(content[start : end + 1])
    if not isinstance(obj, dict):
        raise ValueError("Model response is not a JSON object")
    return obj


def strip_markdown_code_fences(text: str) -> str:
    t = (text or "").strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        t = "\n".join(lines).strip()
    return t


def score_cv(
    *,
    client: Any,
    system_prompt: str,
    job_description: str,
    cv_text: str,
) -> Dict[str, Any]:
    combined_prompt = (
        f"{system_prompt.strip()}\n\n"
        f"Job Description:\n{job_description}\n\n"
        f"Candidate CV:\n{cv_text}\n\n"
        "Return ONLY a valid JSON object."
    )
    last_err: Optional[BaseException] = None
    for attempt in range(1, 4):
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=combined_prompt,
            )
            last_err = None
            break
        except Exception as e:
            last_err = e
            msg = str(e).upper()
            status = getattr(e, "status_code", None) or getattr(e, "code", None)
            is_unavailable = (status == 503) or ("503" in msg) or ("UNAVAILABLE" in msg)
            if is_unavailable and attempt < 3:
                time.sleep(5)
                continue
            raise

    if last_err is not None:
        raise last_err

    content = strip_markdown_code_fences(getattr(resp, "text", "") or "")
    data = parse_model_json(content)
    return data


def progress_color(score: int) -> str:
    if score >= 70:
        return "#16a34a"  # green-600
    if score >= 40:
        return "#ca8a04"  # yellow-600
    return "#dc2626"  # red-600


def render_badges(items, color):
    if not items:
        return "<span style='color:#6b7280;'>None</span>"
    safe = []
    for x in items:
        escaped = x.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe.append(escaped)
    return " ".join(
        f"<span style='display:inline-block;margin:2px 6px 2px 0;padding:4px 10px;border-radius:999px;background:{color};color:white;font-size:12px;line-height:1.2;'>{x}</span>"
        for x in safe
    )


def render_candidate_card(c: CandidateResult) -> None:
    bar_color = progress_color(c.match_score)
    score = c.match_score
    name_html = (
        c.candidate_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if c.candidate_name
        else "Unknown"
    )
    file_html = c.filename.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    summary_html = (c.summary or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    st.markdown(
        f"""
<div style="border:1px solid #e5e7eb;border-radius:14px;padding:16px 16px 14px 16px;margin:12px 0;background:white;">
  <div style="display:flex;gap:12px;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;">
    <div style="min-width:240px;">
      <div style="font-size:18px;font-weight:700;color:#111827;">{name_html}</div>
      <div style="font-size:12px;color:#6b7280;margin-top:2px;">{file_html}</div>
    </div>
    <div style="min-width:220px;flex:1;">
      <div style="display:flex;align-items:center;justify-content:space-between;">
        <div style="font-size:12px;color:#6b7280;">Match score</div>
        <div style="font-size:14px;font-weight:700;color:#111827;">{score}%</div>
      </div>
      <div style="height:10px;background:#f3f4f6;border-radius:999px;overflow:hidden;margin-top:6px;">
        <div style="height:10px;width:{score}%;background:{bar_color};"></div>
      </div>
    </div>
  </div>

  <div style="margin-top:12px;">
    <div style="font-size:12px;font-weight:700;color:#111827;margin-bottom:6px;">Matched skills</div>
    {render_badges(c.matched_skills, "#16a34a")}
  </div>

  <div style="margin-top:10px;">
    <div style="font-size:12px;font-weight:700;color:#111827;margin-bottom:6px;">Missing skills</div>
    {render_badges(c.missing_skills, "#dc2626")}
  </div>

  <div style="margin-top:12px;">
    <div style="font-size:12px;font-weight:700;color:#111827;margin-bottom:6px;">Recruiter summary</div>
    <div style="color:#111827;line-height:1.45;">{summary_html}</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def ensure_finops_state() -> None:
    if "finops" not in st.session_state:
        st.session_state.finops = {
            "latencies_s": [],
            "errors": 0,
            "api_calls": 0,
        }


def finops_add(latency_s: float) -> None:
    ensure_finops_state()
    st.session_state.finops["latencies_s"].append(float(latency_s))
    st.session_state.finops["api_calls"] += 1


def finops_error() -> None:
    ensure_finops_state()
    st.session_state.finops["errors"] += 1


def render_finops_sidebar() -> None:
    ensure_finops_state()
    f = st.session_state.finops
    calls = int(f["api_calls"])
    errors = int(f["errors"])
    latencies = list(f["latencies_s"])
    avg_latency = (sum(latencies) / len(latencies)) if latencies else 0.0

    st.sidebar.subheader("FinOps dashboard")
    st.sidebar.metric("Total API calls", f"{calls:,}")
    st.sidebar.metric("Avg latency per CV", f"{avg_latency:.2f}s")
    st.sidebar.metric("Error count", f"{errors}")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🧾", layout="wide")

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    st.title(APP_TITLE)
    st.caption("Paste a job description, upload CVs, and get ranked candidates with skills and summaries.")

    st.sidebar.header("Job description")
    job_description = st.sidebar.text_area(
        "Paste the job description here",
        height=260,
        placeholder="Responsibilities, requirements, must-haves, nice-to-haves...",
    )

    st.sidebar.divider()
    render_finops_sidebar()

    col_left, col_right = st.columns([1.2, 0.8], gap="large")

    with col_left:
        st.subheader("Upload CVs")
        files = st.file_uploader(
            "Upload one or more PDFs / DOCX files",
            type=["pdf", "docx"],
            accept_multiple_files=True,
        )

        run = st.button(
            "Screen candidates",
            type="primary",
            disabled=(not files or not job_description.strip() or not api_key),
        )

        if not api_key:
            st.warning("Missing `GEMINI_API_KEY`. Add it to your `.env` file.")

        if run:
            try:
                system_prompt = load_system_prompt(SYSTEM_PROMPT_PATH)
            except Exception:
                system_prompt = None

            if system_prompt is None or not system_prompt.strip():
                system_prompt = DEFAULT_SYSTEM_PROMPT

            client = genai.Client(api_key=api_key)
            results: List[CandidateResult] = []

            progress = st.progress(0)
            status = st.empty()

            for idx, uf in enumerate(files):
                status.write(f"Processing `{uf.name}`…")
                try:
                    filename, cv_text = extract_text(uf)
                    if not cv_text.strip():
                        raise ValueError("No extractable text found in document.")

                    t0 = time.perf_counter()
                    data = score_cv(
                        client=client,
                        system_prompt=system_prompt,
                        job_description=job_description,
                        cv_text=cv_text,
                    )
                    latency = time.perf_counter() - t0
                    finops_add(latency)

                    candidate_name = str(data.get("candidate_name", "Unknown") or "Unknown").strip() or "Unknown"
                    match_score = clamp_int(data.get("match_score"), 0, 100, 0)

                    matched_skills = data.get("matched_skills", [])
                    if not isinstance(matched_skills, list):
                        matched_skills = []
                    matched_skills = [str(x).strip() for x in matched_skills if str(x).strip()]

                    missing_skills = data.get("missing_skills", [])
                    if not isinstance(missing_skills, list):
                        missing_skills = []
                    missing_skills = [str(x).strip() for x in missing_skills if str(x).strip()]

                    summary = str(data.get("summary", "") or "").strip()

                    results.append(
                        CandidateResult(
                            filename=filename,
                            candidate_name=candidate_name,
                            match_score=match_score,
                            matched_skills=matched_skills,
                            missing_skills=missing_skills,
                            summary=summary,
                            raw=data,
                        )
                    )
                except Exception as e:
                    finops_error()
                    st.error(f"Error processing `{uf.name}`: {e}")
                finally:
                    progress.progress(int(((idx + 1) / max(1, len(files))) * 100))

            status.empty()
            progress.empty()

            results.sort(key=lambda r: r.match_score, reverse=True)
            st.session_state["latest_results"] = results

    with col_right:
        st.subheader("Ranked candidates")
        results: List[CandidateResult] = st.session_state.get("latest_results", [])
        if not results:
            st.info("Upload CVs and click **Screen candidates** to see results here.")
        else:
            for c in results:
                render_candidate_card(c)


if __name__ == "__main__":
    main()
