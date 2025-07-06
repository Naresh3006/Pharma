import streamlit as st
import re
import google.generativeai as genai
from textwrap import wrap
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# 🔐 Gemini API configuration
GENAI_API_KEY = "AIzaSyBGOXlvs7zKepT18xKJPwwq4KpChFAugMA"
genai.configure(api_key=GENAI_API_KEY)
GEMINI_MODEL = "models/gemini-1.5-flash-latest"

# 🚀 Streamlit setup
st.set_page_config(page_title="Medical Report Generator", layout="centered")
st.title("🩺 Medical Report Generator with PDF")

# 🧾 User Inputs
name = st.text_input("👤 Patient Name")
age = st.number_input("🎂 Age", min_value=0, max_value=120)
mobile = st.text_input("📞 Mobile Number")
query = st.text_input("💊 Enter Disease or Medicine")

# 🧠 Gemini Report Generator
def generate_report(name, age, mobile, query):
    try:
        prompt = f"""
        Write a medically detailed, accurate, and human-friendly 4-paragraph clinical report based on the given patient and medical query.

        Patient Details:
        - Name: {name}
        - Age: {age}
        - Mobile: {mobile}

        Query: "{query}"

        Report Guidelines:
        1. Determine whether the query is a disease, symptom, or medicine.
        2. Provide a likely diagnosis or context.
        3. Suggest appropriate treatment or medication (if applicable).
        4. Recommend specialist referral and give tailored diet/lifestyle advice.
        5. Use clear and professional medical language. Avoid vague terms and unverified assumptions.

        Format as a professional clinical report.
        """

        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()[:4000]  # Cap long responses to avoid PDF issues
    except Exception as e:
        return f"⚠️ Error generating report: {e}"

# 📄 ReportLab PDF Generator (Replaces FPDF)
def generate_pdf(report, filename="medical_report.pdf"):
    try:
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        text_object = c.beginText()
        text_object.setTextOrigin(inch, height - inch)
        text_object.setFont("Helvetica", 12)

        # Clean and wrap text
        clean_text = re.sub(r"[^\x00-\x7F]+", " ", report).replace("\xa0", " ").replace("\t", " ")
        lines = clean_text.replace("\r", "").split("\n")

        for line in lines:
            for wrapped_line in wrap(line, width=100):
                text_object.textLine(wrapped_line)

        c.drawText(text_object)
        c.showPage()
        c.save()
    except Exception as e:
        st.error(f"❌ PDF generation failed: {e}")

# 🎯 Main App Logic
if st.button("🧬 Generate Report"):
    if name and mobile and query:
        # Generate report
        report = generate_report(name, age, mobile, query)

        # Show report
        st.markdown("## 📝 Medical Report")
        st.markdown(report)

        # Generate and offer PDF
        pdf_path = "medical_report.pdf"
        generate_pdf(report, pdf_path)

        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name=pdf_path)
    else:
        st.warning("⚠️ Please complete all input fields.")
