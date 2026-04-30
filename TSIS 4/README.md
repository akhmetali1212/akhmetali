# HR CV Screener

AI-powered CV screening tool for HR managers. Built with **Google Gemini 2.5 Flash** + **Streamlit**.

## Features

- **Upload multiple CVs** (PDF or DOCX) and paste a job description — no manual reading required
- **AI-powered matching** — each CV is scored 0–100% against the job description
- **Ranked results** — candidates sorted by match score, highest first
- **Skills analysis** — matched skills shown as green badges, missing skills as red badges
- **Recruiter summary** — 2–3 sentence AI-generated summary for each candidate
- **FinOps Dashboard** — real-time API call count, error tracking, and average latency

## Project Structure

```
.
├── app.py               # Main Streamlit application
├── system_prompt.txt    # LLM system prompt for CV analysis
├── requirements.txt     # Python dependencies
├── .env                 # API key (not committed to git)
└── README.md
```

## Setup & Run

### 1. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env` file

```
GEMINI_API_KEY=AIza...your-key-here...
```

### 4. Run

```bash
python -m streamlit run app.py
```

The app will open at [http://localhost:8501](http://localhost:8501).

## Usage

1. Paste the **job description** into the sidebar text area
2. Upload one or more **CV files** (PDF or DOCX) in the main area
3. Click **Screen candidates**
4. Ranked candidate cards appear on the right with score, skills, and summary

## D2C Monitoring (Detect to Correct)

| Metric            | Healthy Threshold              |
| ----------------- | ------------------------------ |
| JSON parse errors | 0                              |
| 503 retries       | Max 3 attempts per CV          |
| Avg latency       | < 10 000 ms per CV             |
| Error count       | 0                              |
| API calls         | Tracked per session            |

## IT4IT Value Streams

| Stream | Description |
| ------ | ----------- |
| **S2P** | Automates CV screening for HR managers at SMEs in Almaty — reduces manual review from hours to minutes |
| **R2D** | Architected via AI agent in Cursor; system prompt enforces structured JSON output with strict scoring criteria |
| **R2F** | Streamlit web interface — HR manager uploads CVs and pastes job description, gets ranked results instantly in browser |
| **D2C** | FinOps dashboard tracks API call count, error count, average latency, and automatic retry on 503 errors |**
