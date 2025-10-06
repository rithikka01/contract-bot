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
<img width="1183" height="672" alt="Screenshot (95)" src="https://github.com/user-attachments/assets/c367ef29-c9b2-42a4-94c1-58bc952ade71" />
<img width="1203" height="664" alt="Screenshot (96)" src="https://github.com/user-attachments/assets/664d3d52-96c0-4ea3-a2b9-37914928c77e" />
<img width="1220" height="641" alt="Screenshot (97)" src="https://github.com/user-attachments/assets/a1001494-6f90-4431-a121-4788a3fe1965" />
<img width="1196" height="638" alt="Screenshot (98)" src="https://github.com/user-attachments/assets/db9fb93f-d8f6-4c05-b94f-feca58a94ed2" />





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
