# app.py (updated with PDF export + session-state for AI results)
import streamlit as st
from PyPDF2 import PdfReader
import docx
import tempfile
import os
import re
import json
from datetime import datetime
import random
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from textwrap import wrap

st.set_page_config(page_title="Contract Risk Bot - MVP")
st.title("Contract Risk Bot — MVP")

st.markdown(
    """
    Upload a contract file (PDF, DOCX or TXT).  
    This app extracts text, splits into clauses, runs a simple rule-based risk scorer, and shows flagged clauses.
    """
)

# ---------- helpers: extraction ----------
def extract_text_from_pdf(path):
    try:
        reader = PdfReader(path)
        text_pages = []
        for p in reader.pages:
            txt = p.extract_text()
            if txt:
                text_pages.append(txt)
        return "\n".join(text_pages)
    except Exception as e:
        return f"[PDF extraction error] {e}"

def extract_text_from_docx(path):
    try:
        doc = docx.Document(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        return f"[DOCX extraction error] {e}"

def extract_text_from_txt(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"[TXT extraction error] {e}"

# ---------- improved clause splitter ----------
def simple_clause_split(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n').strip()
    if not text:
        return []

    padded = "\n" + text
    parts = re.split(r'(?m)(?=\n\s*(?:\d+\s*[.)]\s+|[A-Z][A-Za-z0-9\s]{1,60}:))', padded)

    clauses = []
    for p in parts:
        p_clean = "\n".join([ln.strip() for ln in p.splitlines() if ln.strip()])
        if not p_clean:
            continue
        subs = [s.strip() for s in re.split(r'\n{2,}', p_clean) if s.strip()]
        clauses.extend(subs)

    final = []
    for c in clauses:
        if len(c) < 10:
            if re.match(r'^[A-Z0-9 &]{3,}$', c):
                final.append(c)
            else:
                continue
        else:
            final.append(c)

    if len(final) < 3:
        sents = [s.strip() for s in re.split(r'(?<=[.?!])\s+', text) if len(s.strip())>5]
        return sents

    return final

# ---------- rule-based risk engine ----------
RISK_KEYWORDS = {
    "high": [
        "indemnif", "indemnity", "liabilit", "liability", "penalt", "liquidated damages",
        "auto-?renew", "automatic renewal", "exclusive", "exclusivity", "assignment without",
        "assignment", "terminate without", "termination without", "waive", "waiver"
    ],
    "medium": [
        "notice", "governing law", "jurisdiction", "dispute", "confidential", "confidentiality",
        "non-compete", "non compete", "subcontract", "termination", "breach", "limitation of liability"
    ],
    "low": [
        "payment", "invoice", "currency", "delivery", "service level", "slas", "force majeure"
    ]
}
LEVEL_WEIGHT = {"high": 40, "medium": 15, "low": 5}

def score_clause(text):
    t = text.lower()
    score = 0
    matched = []
    for level, kws in RISK_KEYWORDS.items():
        for kw in kws:
            if re.search(re.escape(kw), t):
                score += LEVEL_WEIGHT[level]
                matched.append((level, kw))
    m = re.search(r'\b(\d{1,2})\s*(day|days|month|months)\b', t)
    if m:
        try:
            num = int(m.group(1))
            unit = m.group(2)
            if unit.startswith("day") and num <= 15:
                score += 10
                matched.append(("medium", f"short_notice_{num}_days"))
        except:
            pass
    score = min(100, score)
    return score, matched

def analyze_clauses(clauses):
    flagged = []
    for idx, c in enumerate(clauses):
        s, matched = score_clause(c)
        if s > 0:
            flagged.append({"index": idx, "clause": c, "score": s, "matches": matched})
    flagged_sorted = sorted(flagged, key=lambda x: x["score"], reverse=True)
    return flagged_sorted

# ------- Mock AI helpers -------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_MOCK_AI_DEFAULT = True

def summarize_matches_to_risks(matches):
    risks = []
    seen = set()
    for lvl, kw in matches:
        k = kw.lower()
        if "indemnif" in k or "indemnity" in k:
            if "Indemnity may expose you to large financial liability." not in seen:
                risks.append("Indemnity language may require you to pay the other party's losses.")
                seen.add("Indemnity may expose you to large financial liability.")
        if "liabilit" in k or "liability" in k:
            if "Unlimited liability could be financially risky." not in seen:
                risks.append("Liability terms may expose you to large or unlimited damages.")
                seen.add("Unlimited liability could be financially risky.")
        if "auto-renew" in k or "automatic renewal" in k or "auto-?renew" in k:
            if "Auto-renew can lock you into long commitments without notice." not in seen:
                risks.append("Automatic renewal may lock you into longer commitments; you may miss opt-out windows.")
                seen.add("Auto-renew can lock you into long commitments without notice.")
        if "terminate" in k or "short_notice" in k:
            if "Short termination notice reduces your time to respond." not in seen:
                risks.append("Short termination or notice periods limit your ability to respond/exit cleanly.")
                seen.add("Short termination notice reduces your time to respond.")
        if "confidential" in k or "confidentiality" in k:
            if "Broad confidentiality might limit your normal business operations." not in seen:
                risks.append("Very broad confidentiality clauses may restrict necessary business communications.")
                seen.add("Broad confidentiality might limit your normal business operations.")
        if "governing law" in k or "jurisdiction" in k:
            if "Non-India jurisdiction increases costs if disputes arise." not in seen:
                risks.append("Governing law or foreign jurisdiction may increase legal cost and complexity in India.")
                seen.add("Non-India jurisdiction increases costs if disputes arise.")
        if "payment" in k or "invoice" in k:
            if "Unclear payment terms could delay revenue." not in seen:
                risks.append("Unclear payment or invoice terms could delay payments.")
                seen.add("Unclear payment terms could delay revenue.")
    if not risks:
        risks.append("This clause may carry standard contractual risk; consult a lawyer for certainty.")
    return risks

def mock_ai_analysis(clause_text, clause_index, filename, matched=None):
    short = clause_text.strip()
    if len(short) > 300:
        short_preview = short[:300].rsplit(".", 1)[0] + "..."
    else:
        short_preview = short

    explanation = f"This clause says: {short_preview}. In simple terms, it describes the contract's position regarding the stated subject."
    risks = summarize_matches_to_risks(matched or [])
    if random.random() < 0.15:
        risks.append("May require additional clarification around timelines and responsibilities.")
    suggestion = "Consider limiting obligations, capping liability to direct damages only, adding a clear notice period of at least 30 days, and including a mutual indemnity (if appropriate)."
    if matched:
        kws = [kw for lvl, kw in matched]
        if any("indemn" in kw for kw in kws):
            suggestion = "Consider narrowing indemnity: require direct, proven loss only; include notice and defence rights; add a monetary cap."
        elif any("auto-renew" in kw or "renew" in kw for kw in kws):
            suggestion = "Consider replacing automatic renewal with explicit renewal or add a short opt-out window of at least 30 days prior to renewal."
        elif any("short_notice" in kw for lvl, kw in matched):
            suggestion = "Increase the notice/termination period to at least 30 days to reduce operational risk."

    return {"explanation": explanation, "risks": risks, "suggestion": suggestion, "mock": True}

def analyze_with_ai(clause_text, clause_index, filename, matched=None, timeout_s=20):
    if OPENAI_API_KEY and not USE_MOCK_AI_DEFAULT:
        return {"error": "Real AI not enabled in this demo."}
    return {"ok": True, "result": mock_ai_analysis(clause_text, clause_index, filename, matched=matched)}

# ---------- PDF report generator ----------
def create_pdf_bytes(audit, clauses, ai_results):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    x = margin
    y = height - margin

    def draw_title(text):
        nonlocal y
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x, y, text)
        y -= 10 * mm

    def draw_h1(text):
        nonlocal y
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, text)
        y -= 7 * mm

    def draw_text_block(text, indent=0, size=10, leading=12):
        nonlocal y
        c.setFont("Helvetica", size)
        lines = []
        for para in str(text).split("\n"):
            wrapped = wrap(para, 100 - indent//6)
            if not wrapped:
                lines.append("")
            else:
                lines.extend(wrapped)
        for line in lines:
            if y < margin + 30:
                c.showPage()
                y = height - margin
            c.drawString(x + indent, y, line)
            y -= leading

    # Title & header
    draw_title("Contract Analysis Report")
    c.setFont("Helvetica", 10)
    c.drawString(x, y + 6*mm, f"File: {audit.get('filename','-')}")
    c.drawString(x + 250, y + 6*mm, f"Generated: {audit.get('timestamp','-')}")
    y -= 12*mm

    # Summary
    draw_h1("Summary")
    draw_text_block(f"Overall Risk Score: {audit.get('overall_score',0)} / 100", indent=0)
    draw_text_block(f"Number of Clauses Detected: {audit.get('num_clauses', len(clauses))}", indent=0)
    draw_text_block(f"Flagged Clauses: {audit.get('flagged_count', len(audit.get('flagged',[]))) }", indent=0)
    y -= 3*mm

    # Flagged clauses
    draw_h1("Flagged Clauses (Top)")
    for f in audit.get("flagged", [])[:20]:
        idx = f.get("index", -1) + 1
        score = f.get("score", 0)
        matches = ", ".join([f"{lvl}:{kw}" for (lvl, kw) in f.get("matches", [])]) if f.get("matches") else "-"
        draw_text_block(f"Clause {idx} — Score: {score} — Matches: {matches}", indent=0)
        draw_text_block(f"{f.get('clause','')}", indent=6, size=9, leading=11)
        y -= 2*mm

    # AI results
    if ai_results:
        draw_h1("AI / Explanations & Suggestions")
        for r in ai_results:
            idx = r.get("index", -1) + 1
            draw_text_block(f"Clause {idx} — Rule score: {r.get('score',0)}", indent=0)
            ai = r.get("ai", {})
            if ai.get("ok"):
                res = ai.get("result", {})
                draw_text_block("Explanation:", indent=6)
                draw_text_block(res.get("explanation","(none)"), indent=12)
                draw_text_block("Risks:", indent=6)
                for rr in res.get("risks", []):
                    draw_text_block(f"- {rr}", indent=12)
                draw_text_block("Suggestion:", indent=6)
                draw_text_block(res.get("suggestion","(none)"), indent=12)
            else:
                draw_text_block("AI Analysis: (error or not available)", indent=6)
            y -= 2*mm

    # Footer / disclaimer
    if y < margin + 60:
        c.showPage()
        y = height - margin
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(x, margin + 10, "This report is an automatically generated analysis (MVP). Not legal advice. Consult a qualified lawyer for binding recommendations.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

# ---------- UI: file uploader & processing ----------
uploaded = st.file_uploader("Upload contract (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

overall = 0
clauses = []
flagged = []

if uploaded is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix="."+uploaded.name.split(".")[-1]) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    ext = uploaded.name.split(".")[-1].lower()
    st.info(f"Processing file: {uploaded.name}  —  detected type: {ext.upper()}")

    if ext == "pdf":
        full_text = extract_text_from_pdf(tmp_path)
    elif ext == "docx":
        full_text = extract_text_from_docx(tmp_path)
    else:
        full_text = extract_text_from_txt(tmp_path)

    try:
        os.remove(tmp_path)
    except Exception:
        pass

    if full_text.startswith("[") and "error" in full_text.lower():
        st.error(full_text)
    elif not full_text or len(full_text.strip()) == 0:
        st.warning("No text found in the uploaded file.")
    else:
        st.success("Text extracted successfully!")

        with st.expander("Preview extracted text (first 3000 chars)"):
            st.text(full_text[:3000])

        clauses = simple_clause_split(full_text)
        st.write(f"Detected **{len(clauses)}** clauses/segments.")

        # analyze clauses and compute flagged
        flagged = analyze_clauses(clauses)

        # compute overall if flagged present
        if flagged:
            avg_flagged = sum(f["score"] for f in flagged) / len(flagged)
            overall = int((avg_flagged * (len(flagged) / max(1, len(clauses)))) )
            overall = min(100, overall)
        else:
            overall = 0

        # show results (mock AI integrated)
        if not flagged:
            st.success("No risky clauses detected by the rule-based engine (basic checks).")
        else:
            st.markdown("## ⚠️ Risk Summary")
            st.metric("Overall contract risk (0-100)", overall)
            st.write(f"Flagged clauses: {len(flagged)} (out of {len(clauses)})")

            st.markdown("### Flagged clauses (top results)")
            for f in flagged[:10]:
                idx = f["index"] + 1
                st.write(f"**Clause {idx} — Risk score: {f['score']}**")
                matches = ", ".join([f"{lvl}:{kw}" for (lvl, kw) in f["matches"]]) if f.get("matches") else "—"
                st.caption(f"Matched: {matches}")
                st.write(f["clause"])
                st.write("---")

            st.markdown("### 🔍 Clause explanations & suggestions (Mock AI)")
            use_mock = st.checkbox("Use Mock AI (no API key)", value=True)
            max_analyze = st.number_input("Max flagged clauses to analyze (top N)", min_value=1, max_value=min(10, len(flagged)), value=min(3, len(flagged)), step=1)

            if st.button("Run clause explanations & suggestions (mock)"):
                top_to_analyze = flagged[:int(max_analyze)]
                ai_results = []
                with st.spinner("Generating explanations (mock) — very fast..."):
                    for f in top_to_analyze:
                        clause_text = f["clause"]
                        matched = f.get("matches", [])
                        ai_resp = analyze_with_ai(clause_text, f["index"]+1, uploaded.name, matched=matched)
                        ai_results.append({"index": f["index"], "score": f["score"], "ai": ai_resp})
                # store results in session so PDF download can include them
                st.session_state["last_ai_results"] = ai_results
                st.markdown("#### Results")
                for r in ai_results:
                    st.write(f"**Clause {r['index']+1} — rule-score {r['score']}**")
                    if not r.get("ai"):
                        st.error("No response")
                        continue
                    if r["ai"].get("ok"):
                        res = r["ai"]["result"]
                        st.markdown("**Explanation:**")
                        st.write(res.get("explanation", "(none)"))
                        st.markdown("**Risks:**")
                        for rr in res.get("risks", []):
                            st.write(f"- {rr}")
                        st.markdown("**Suggestion / Alternative clause:**")
                        st.write(res.get("suggestion","(none)"))
                        if res.get("mock"):
                            st.caption("Generated by mock AI for demo — replace with GPT-4/Claude when you have an API key.")
                    else:
                        st.error(f"AI error: {r['ai'].get('error')}")
                        if r['ai'].get('raw'):
                            st.text(r['ai']['raw'][:1000])

        # Show all clauses option
        if st.checkbox("Show all detected clauses"):
            st.markdown("### All clauses")
            for i, c in enumerate(clauses, 1):
                st.write(f"**Clause {i}:**")
                st.write(c)
                st.write("---")

        # Prepare ai_results for PDF (use saved session results if available)
        ai_results_for_pdf = st.session_state.get("last_ai_results", None) if "last_ai_results" in st.session_state else None
        if not ai_results_for_pdf:
            ai_results_for_pdf = [{"index": f["index"], "score": f["score"], "ai": {"ok": False}} for f in flagged[:5]]

        # Build audit object (same as JSON)
        audit = {
            "filename": uploaded.name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "num_clauses": len(clauses),
            "flagged_count": len(flagged),
            "overall_score": overall if flagged else 0,
            "flagged": flagged
        }

        # JSON download
        json_bytes = json.dumps(audit, indent=2).encode("utf-8")
        st.download_button("Download analysis (JSON)", data=json_bytes, file_name="analysis_report.json", mime="application/json")

        # PDF download
        try:
            pdf_bytes = create_pdf_bytes(audit, clauses, ai_results_for_pdf)
            st.download_button("Download analysis (PDF)", data=pdf_bytes, file_name="contract_analysis_report.pdf", mime="application/pdf")
            st.success("PDF and JSON ready to download.")
        except Exception as e:
            st.error(f"PDF generation error: {e}")

# Footer / disclaimer
st.markdown("---")
st.caption("This is an MVP rule-based analysis for demo only. Not legal advice. For real legal review consult a qualified lawyer.")
