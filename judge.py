import google.generativeai as genai
import json

# Set your API key
genai.configure(api_key="YOUR_API_KEY")

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    system_instruction="""
You are a Senior Architect and QA Judge Agent.

Your task:
Evaluate if the provided code complies with the PRD.

Rules:
- Score compliance from 0 to 100.
- Check:
  1. Functional requirements
  2. Error handling
  3. Security risks
  4. Architecture constraints (e.g., no external APIs if on-premise required)
- If external API is used when PRD says local only → major violation.
- If sensitive data is printed → security issue.
- If error handling missing → requirement not met.

Output ONLY valid JSON in this format:

{
  "compliance_score": number,
  "status": "PASS" or "FAIL",
  "audit_log": [
    {
      "requirement": "text",
      "met": true/false,
      "comment": "text"
    }
  ],
  "security_check": "Safe" or "Unsafe"
}
"""
)

# Read files
with open("prd.txt", "r") as f:
    prd = f.read()

with open("code_submission.py", "r") as f:
    code = f.read()

prompt = f"""
PRD:
{prd}

CODE:
{code}
"""

response = model.generate_content(prompt)

# Save result
result_text = response.text.strip()

with open("compliance_report.json", "w") as f:
    f.write(result_text)

print("Report saved to compliance_report.json")
