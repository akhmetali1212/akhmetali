# TSIS 2: Judge Agent for Otbasy Companion

## Project Information
- **Course:** TSIS
- **Author:** Akhmetali Yessenbayev
- **Year:** 2026

---

## Overview
This project implements a **Judge Agent** — an AI system that evaluates whether developer code complies with a Product Requirements Document (PRD). 

The agent simulates the role of a **Senior Architect** and checks:

- Functional requirements  
- Error handling  
- Security issues  
- Architectural constraints (on-premise requirement)  

The result is generated as a JSON compliance report.

---

## Connection to TSIS 1
The project is based on **Otbasy Companion AI**. Since banking systems require high security, the Judge Agent ensures that:

- No external APIs are used  
- Sensitive data is protected  
- Code meets system requirements  

---

## Project Structure

TSIS2/
├── prd.txt
├── code_submission.py
├── judge.py
├── compliance_report.json
└── README.md


---

## Files Description

- **prd.txt** – system requirements  
- **code_submission.py** – example developer code with intentional issues  
- **judge.py** – AI-based evaluation script using Gemini  
- **compliance_report.json** – generated compliance result  

---

## Technologies

- Python 3  
- Google Gemini API  
- JSON  

---

## How to Run

1. Install dependencies:

```bash
pip install google-generativeai
Set your API key in judge.py

Run the script:

python judge.py
Output will be saved as compliance_report.json

Result
The system automatically compares PRD and code and produces:

Compliance score (0–100)

PASS / FAIL status

Requirement audit log

Security assessment
