import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import re
import google.generativeai as genai

# Page config
st.set_page_config(page_title="Medical Report Generator", layout="centered")
st.title("🩺 Medical Report Generator with PDF")

# Gemini API hardcoded
GENAI_API_KEY = "AIzaSyBGOXlvs7zKepT18xKJPwwq4KpChFAugMA"
genai.configure(api_key=GENAI_API_KEY)

# Excel files
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

# UI inputs
name = st.text_input("Patient Name")
age = st.number_input("Age", min_value=0, max_value=120)
mobile = st.text_input("Mobile Number")
query = st.text_input("Enter Disease or Medicine")

# Generate report using Gemini
def generate_report(name, age, mobile, disease, doctor_type, medicine, diet):
    try:
        prompt = f"""
        Write a professional medical report in 4 paragraphs:
        1. Patient Info: Name: {name}, Age: {age}, Mobile: {mobile}
        2. Description of the disease: {disease}
        3. Doctor type: {doctor_type}, Medicine: {medicine}
        4. Dietary and lifestyle advice: {diet}
        """
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Error generating report: {e}"

# Generate PDF from report
def generate_pdf(report, filename="medical_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    text = re.sub(r"[^\x00-\x7F]+", "", report)  # Remove unsupported characters
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)

# Main logic
if st.button("Generate Report"):
    if name and mobile and query:
        rec = df[df.apply(lambda r: r.astype(str).str.contains(query, case=False, na=False).any(), axis=1)]
        if not rec.empty:
            rec = rec.iloc[0]
            report = generate_report(
                name, age, mobile,
                rec.get("Disease", "unspecified"),
                rec.get("Doctor Type", "general physician"),
                rec.get("Medicine Name", "medicine"),
                rec.get("Diet Advice", "healthy diet"),
            )
            st.markdown("## 📝 Medical Report")
            st.markdown(report)
            pdf_file = "medical_report.pdf"
            generate_pdf(report, pdf_file)
            with open(pdf_file, "rb") as f:
                st.download_button("📥 Download PDF", f, file_name=pdf_file)
        else:
            st.warning("No matching record found.")
    else:
        st.warning("Please fill all fields.")
