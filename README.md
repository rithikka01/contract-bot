Contract Risk Bot — MVP  

AI-assisted legal contract analyzer that helps small & medium businesses identify risks, explain clauses, and download a report — all in simple language.



Overview : 
This GenAI-powered MVP analyzes legal contracts to highlight potential risks and explain them in business-friendly terms.  
It supports PDF, DOCX, and TXT uploads, performs rule-based risk scoring, and provides **mock AI explanations & safer alternatives.  
Finally, users can download JSON & PDF reports for legal review — all within 2 minutes.



Key Features :

✅ Upload PDF / DOCX / TXT contracts  
✅ Extract & split into clauses  
✅ Rule-based clause risk scoring (High / Medium / Low)  
✅ Mock AI explanations & safer clause suggestions  
✅ JSON + PDF report generation with audit details  
✅ Streamlit web UI (no setup complexity)  
✅ Offline demo mode (no API key required)



Tech Stack
| Component | Tool / Library |
|------------|----------------|
| Frontend/UI | Streamlit |
| Backend | Python 3 |
| NLP | spaCy, NLTK |
| File Handling | PyPDF2, python-docx |
| Report Export | reportlab |
| Optional AI | OpenAI GPT-4 / Claude 3 (disabled in demo) |

📸 Screenshots

<img width="1217" height="679" alt="Screenshot (94)" src="https://github.com/user-attachments/assets/95f1e4b1-56d9-4a0b-965a-d88f5d1d2c14" />




How to Run Locally

```bash
# 1️⃣ Clone this repo
git clone https://github.com/rithikka01/contract-bot.git
cd contract-bot

# 2️⃣ Create & activate virtual environment
python -m venv venv
venv\Scripts\Activate.ps1   # (PowerShell)
# or
source venv/Scripts/activate  # (Git Bash)

# 3️⃣ Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 4️⃣ Run the app
streamlit run app.py


Disclaimer

This is a prototype for educational purposes only —
It does not constitute legal advice.
For real legal consultation, always contact a qualified professional.

⭐ If you found this project interesting, give it a star on GitHub!
