# Contract Risk Bot — MVP

**One-line:** MVP web app that extracts contract text (PDF/DOCX/TXT), splits into clauses, performs a rule-based risk analysis, and provides mock AI explanations & suggestions. Exports JSON and PDF reports.

## What it does (MVP)
- Upload PDF / DOCX / TXT contract files.
- Extracts text and splits into clauses.
- Rule-based risk scoring (flags clauses using high/medium/low keyword rules).
- Mock AI explanations & suggestions (demo mode) for flagged clauses — replaceable with GPT-4/Claude later.
- Downloadable analysis: JSON & PDF (professional-style report).
- Audit trail saved in the downloadable report.

## Tech stack
- Python 3, Streamlit (UI)
- PyPDF2, python-docx (text extraction)
- spaCy, NLTK (NLP — model included)
- reportlab (PDF generation)
- (Optional) OpenAI GPT-4 support — toggled off by default / mock-first

## How to run (local)
1. Clone the repo:
   ```bash
   git clone https://github.com/<your-username>/contract-bot.git
   cd contract-bot
