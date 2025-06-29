import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import re
import google.generativeai as genai
from textwrap import wrap

# 🔐 Gemini API configuration
GENAI_API_KEY = "AIzaSyBGOXlvs7zKepT18xKJPwwq4KpChFAugMA"
genai.configure(api_key=GENAI_API_KEY)
GEMINI_MODEL = "models/gemini-1.5-flash-latest"

# 🚀 Streamlit setup
st.set_page_config(page_title="Medical Report Generator", layout="centered")
st.title("🩺 Medical Report Generator with PDF")

# 📂 Excel sources
excel_files = [
    "Antibiotic_Tablets_Dataset (4).xlsx",
    "Anti_Diabetic_Drugs.xlsx",
    "Anti_Hypertensive_Drugs_Dataset_Full.xlsx",
    "Anti_neoplastic_Drugs_Dataset_Complete.xlsx",
    "Anti_Tubercular_Agents (1).xlsx",
]

@st.cache_data
def load_data():
    dfs = [pd.read_excel(f) for f in excel_files if os.path.exists(f)]
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

df = load_data()

# 🧾 User Input
name = st.text_input("Patient Name")
age = st.number_input("Age", min_value=0, max_value=120)
mobile = st.text_input("Mobile Number")
query = st.text_input("Enter Disease or Medicine")

# 🧠 Gemini Report Generator
def generate_report(name, age, mobile, query, matched_data=None):
    try:
        if matched_data is not None:
            disease = matched_data.get("Disease", query)
            doctor_type = matched_data.get("Doctor Type", "General Physician")
            medicine = matched_data.get("Medicine Name", query)
            diet = matched_data.get("Diet Advice", "Follow a healthy lifestyle.")

            prompt = f"""
            Write a personalized 4-paragraph clinical report for a patient.

            Patient:
            - Name: {name}
            - Age: {age}
            - Mobile: {mobile}

            Diagnosis:
            - {disease}

            Medication:
            - {medicine}
              Explain its purpose, how to use it, and possible side effects.

            Referral:
            - Refer to: {doctor_type}

            Lifestyle & Diet:
            - {diet}
            """
        else:
            prompt = f"""
            Write a medically accurate 4-paragraph report for the patient below.

            Patient:
            - Name: {name}
            - Age: {age}
            - Mobile: {mobile}

            Complaint or Query: "{query}"

            Tasks:
            1. Determine whether the query is a disease, symptom, or medicine.
            2. Provide diagnosis insight.
            3. Suggest a suitable treatment or management plan (medications if applicable).
            4. Recommend a doctor/specialist.
            5. Give diet/lifestyle advice tailored to the situation.

            Avoid vague language and base assumptions on clinical likelihood.
            """

        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        return f"⚠️ Error generating report: {e}"

# 📄 PDF Generator (Robust for Streamlit Cloud)
def generate_pdf(report, filename="medical_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    # Clean text
    clean_text = re.sub(r"[^\x00-\x7F]+", " ", report)
    clean_text = clean_text.replace("\xa0", " ").replace("\t", " ")

    max_line_length = 90

    for paragraph in clean_text.split("\n"):
        words = paragraph.split()
        line = ""

        for word in words:
            if len(word) > max_line_length:
                if line:
                    pdf.multi_cell(0, 10, line)
                    line = ""
                for part in wrap(word, max_line_length):
                    pdf.multi_cell(0, 10, part)
            else:
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
        matched = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)]
        record = matched.iloc[0] if not matched.empty else None

        report = generate_report(name, age, mobile, query, matched_data=record)

        st.markdown("## 📝 Medical Report")
        st.markdown(report)

        pdf_path = "medical_report.pdf"
        generate_pdf(report, pdf_path)
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download PDF", f, file_name=pdf_path)
    else:
        st.warning("⚠️ Please complete all input fields.")
