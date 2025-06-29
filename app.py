import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import re
import google.generativeai as genai

# ✅ Gemini API key (hardcoded - not secure for production)
GENAI_API_KEY = "AIzaSyBGOXlvs7zKepT18xKJPwwq4KpChFAugMA"
genai.configure(api_key=GENAI_API_KEY)

# ✅ Gemini 1.5 Flash model
GEMINI_MODEL = "models/gemini-1.5-flash-latest"

# ✅ Streamlit setup
st.set_page_config(page_title="Medical Report Generator", layout="centered")
st.title("🩺 Medical Report Generator with PDF")

# ✅ Load Excel datasets
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

# ✅ Input fields
name = st.text_input("Patient Name")
age = st.number_input("Age", min_value=0, max_value=120)
mobile = st.text_input("Mobile Number")
query = st.text_input("Enter Disease or Medicine")

# ✅ Generate report using Gemini
def generate_report(name, age, mobile, disease, doctor_type, medicine, diet):
    try:
        prompt = f"""
        Write a professional and empathetic 4-paragraph medical report based on the following details:

        1. Patient Information:
           - Name: {name}
           - Age: {age}
           - Mobile: {mobile}

        2. Disease Description:
           - {disease}

        3. Recommended Doctor & Medicine:
           - Doctor Type: {doctor_type}
           - Medicine: {medicine}

        4. Dietary and Lifestyle Advice:
           - {diet}
        """
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Error generating report: {e}"

# ✅ Generate PDF from report (safe text wrapping)
def generate_pdf(report, filename="medical_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    clean_text = re.sub(r"[^\x00-\x7F]+", "", report)  # Remove non-ASCII chars

    for paragraph in clean_text.split("\n"):
        while len(paragraph) > 90:
            split_index = paragraph.rfind(" ", 0, 90)
            if split_index == -1:
                split_index = 90
            pdf.multi_cell(0, 10, paragraph[:split_index])
            paragraph = paragraph[split_index:].lstrip()
        if paragraph:
            pdf.multi_cell(0, 10, paragraph)

    pdf.output(filename)

# ✅ Main logic on button click
if st.button("Generate Report"):
    if name and mobile and query:
        match = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)]
        if not match.empty:
            rec = match.iloc[0]
            report = generate_report(
                name, age, mobile,
                rec.get("Disease", "Unspecified"),
                rec.get("Doctor Type", "General Physician"),
                rec.get("Medicine Name", "Appropriate medicine"),
                rec.get("Diet Advice", "General healthy diet")
            )

            st.markdown("## 📝 Medical Report")
            st.markdown(report)

            # Generate and offer PDF download
            pdf_file = "medical_report.pdf"
            generate_pdf(report, pdf_file)
            with open(pdf_file, "rb") as f:
                st.download_button("📥 Download PDF", f, file_name=pdf_file)
        else:
            st.warning("❗ No matching medicine or disease found in the database.")
    else:
        st.warning("⚠️ Please fill all required fields.")
