import streamlit as st
import re
import google.generativeai as genai
from textwrap import wrap
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# 🔐 Gemini API configuration
GENAI_API_KEY = "AIzaSyCUisl7l4yQCHrPaGIkHnflyVqfz9UHWwM"
genai.configure(api_key=GENAI_API_KEY)
GEMINI_MODEL = "models/gemini-1.5-flash-latest"

# 🚀 Streamlit setup
st.set_page_config(page_title="Medical Report Generator", layout="centered")
st.title("🩺 Medical Report Generator with PDF")

# 🧾 User Inputs
name = st.text_input("👤 Patient Name")
age = st.number_input("🎂 Age", min_value=0, max_value=120)
gender = st.selectbox("⚧ Gender", ["Male", "Female", "Other"])
weight = st.number_input("⚖️ Weight (kg)", min_value=0.0, max_value=300.0, step=0.1)
mobile = st.text_input("📞 Mobile Number")
query = st.text_input("💊 Enter Disease or Medicine")

# 🧠 Gemini Report Generator
def generate_report(name, age, gender, weight, mobile, query):
    try:
        prompt = f"""
        You are a medical professional generating a clinical report for a patient based on a medical query.

        Patient Details:
        - Name: {name}
        - Age: {age}
        - Gender: {gender}
        - Weight: {weight} kg
        - Mobile: {mobile}
        - Query: "{query}"

        First determine if the query is a **disease** or a **medicine**.
        
        🔹 If it's a disease:
        1. First paragraph: Explain the disease and standard medications used to treat it.
        2. Second paragraph: Explain dosage and timing of those medications, considering the patient's age, gender, and weight when relevant.
        3. Third paragraph: Describe the contraindications of those medications and the symptoms of the disease.

        🔹 If it's a medicine:
        1. First paragraph: Describe the medicine, its category, and common usage.
        2. Second paragraph: Explain the dosage and appropriate timing, considering the patient's age, gender, and weight when relevant.
        3. Third paragraph: List contraindications and symptoms it is used to treat.

        Use a clear, concise, and medically professional tone.
        Each paragraph should be detailed and informative.
        """

        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()[:4000]
    except Exception as e:
        return f"⚠️ Error generating report: {e}"

# 📄 ReportLab PDF Generator
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
    if name and mobile and query and weight > 0:
        report = generate_report(name, age, gender, weight, mobile, query)

        st.markdown("## 📝 Medical Report")
        st.markdown(report)

        pdf_path = "medical_report.pdf"
        generate_pdf(report, pdf_path)

        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name=pdf_path)
    else:
        st.warning("⚠️ Please complete all input fields.")
