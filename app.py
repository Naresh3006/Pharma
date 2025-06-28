import streamlit as st
import pandas as pd
import requests
from fpdf import FPDF
import os
import re

# Page configuration
st.set_page_config(page_title="Medical Report Generator", layout="centered")
st.title("🩺 Medical Report Generator with PDF")

# Hugging Face API
HF_API_KEY = st.secrets["HF_API_KEY"]
LLM_ENDPOINT = "https://api-inference.huggingface.co/models/TheBloke/Mistral-7B-Instruct-v0.2-GGUF"  # free open-source model

# Excel files
excel_files = [
    "Antibiotic_Tablets_Dataset (4).xlsx",
    "Anti_Diabetic_Drugs.xlsx",
    "Anti_Hypertensive_Drugs_Dataset_Full.xlsx",
    "Anti_neoplastic_Drugs_Dataset_Complete.xlsx",
    "Anti_Tubercular_Agents (1).xlsx",
]

# Load data
@st.cache_data
def load_combined_data():
    dfs = [pd.read_excel(file) for file in excel_files if os.path.exists(file)]
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

df = load_combined_data()

# UI Inputs
name = st.text_input("Patient Name")
age = st.number_input("Age", min_value=0, max_value=120)
mobile = st.text_input("Mobile Number")
query = st.text_input("Enter Disease or Medicine")

# Clean text for PDF (remove non-ASCII characters)
def clean_text_for_pdf(text):
    return re.sub(r"[^\x00-\x7F]+", "", text)

# Generate PDF
def generate_pdf(report_text, filename="medical_report.pdf"):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        clean_text = clean_text_for_pdf(report_text)
        for line in clean_text.split('\n'):
            pdf.multi_cell(0, 10, line)
        pdf.output(filename)
        return True
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return False

# LLaMA-based report generation
def generate_report_llama(name, age, mobile, disease, doctor_type, medicine, diet):
    prompt = f"""
    Write a professional medical report for:
    - Patient Name: {name}
    - Age: {age}
    - Mobile: {mobile}
    - Disease: {disease}
    - Doctor Type: {doctor_type}
    - Medicine: {medicine}
    - Diet Advice: {diet}

    Structure:
    1. Patient intro
    2. Explanation of condition
    3. Doctor & medicine suggestion
    4. Lifestyle & diet guidance
    """

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}"
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": 0.7,
            "max_new_tokens": 512,
            "do_sample": True,
        }
    }

    try:
        response = requests.post(LLM_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result[0]['generated_text'].strip()
    except Exception as e:
        return f"Error generating report: {e}"

# Main logic
if st.button("Generate Report"):
    if name and mobile and query:
        filtered = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)]

        if not filtered.empty:
            record = filtered.iloc[0]
            disease = record.get("Disease", "unspecified condition")
            doctor_type = record.get("Doctor Type", "general physician")
            medicine = record.get("Medicine Name", "a medicine")
            diet = record.get("Diet Advice", "a healthy diet")

            report = generate_report_llama(name, age, mobile, disease, doctor_type, medicine, diet)

            st.markdown("## 📝 Medical Report")
            st.markdown(report)

            pdf_filename = "medical_report.pdf"
            if generate_pdf(report, pdf_filename) and os.path.exists(pdf_filename):
                with open(pdf_filename, "rb") as f:
                    st.download_button("📥 Download PDF", f, file_name=pdf_filename)
        else:
            st.warning("No relevant data found for your query.")
    else:
        st.warning("Please fill all required fields (Name, Mobile, and Query).")
