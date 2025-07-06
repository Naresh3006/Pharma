import streamlit as st
import re
from fpdf import FPDF
import google.generativeai as genai
from textwrap import wrap

# 🔐 Gemini API configuration
GENAI_API_KEY = "AIzaSyBGOXlvs7zKepT18xKJPwwq4KpChFAugMA"
genai.configure(api_key=GENAI_API_KEY)
GEMINI_MODEL = "models/gemini-1.5-flash-latest"

# 🚀 Streamlit setup
st.set_page_config(page_title="Medical Report Generator", layout="centered")
st.title("🩺 Medical Report Generator with PDF")

# 🧾 User Input
name = st.text_input("Patient Name")
age = st.number_input("Age", min_value=0, max_value=120)
mobile = st.text_input("Mobile Number")
query = st.text_input("Enter Disease or Medicine")

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
        return response.text.strip()

    except Exception as e:
        return f"⚠️ Error generating report: {e}"

# 📄 PDF Generator
def generate_pdf(report, filename="medical_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    clean_text = re.sub(r"[^\x00-\x7F]+", " ", report).replace("\xa0", " ").replace("\t", " ")
    max_line_length = 90

    # Adjusting for very long words by wrapping them
    max_word_length = 60  # Max length for unbreakable words

    for paragraph in clean_text.split("\n"):
        words = paragraph.split()
        line = ""

        for word in words:
            # If a word is too long, break it into smaller parts
            if len(word) > max_word_length:
                if line:
                    pdf.multi_cell(0, 10, line)
                    line = ""
                for part in wrap(word, max_word_length):
                    pdf.multi_cell(0, 10, part)
            else:
                # Line breaking logic
                if len(line + " " + word) <= max_line_length:
                    line += " " + word if line else word
                else:
                    pdf.multi_cell(0, 10, line)
                    line = word

        if line:
            pdf.multi_cell(0, 10, line)

    try:
        pdf.output(filename)
    except Exception as e:
        st.error(f"❌ PDF generation failed: {e}")

# 🧩 Main Button Logic
if st.button("Generate Report"):
    if name and mobile and query:
        # Generate the report using Gemini
        report = generate_report(name, age, mobile, query)

        # Display the report in Streamlit
        st.markdown("## 📝 Medical Report")
        st.markdown(report)

        # Generate and download the PDF version of the report
        pdf_path = "medical_report.pdf"
        generate_pdf(report, pdf_path)

        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name=pdf_path)
    else:
        st.warning("⚠️ Please complete all input fields.")
