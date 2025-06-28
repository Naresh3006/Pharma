import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import requests

# Set page configuration
st.set_page_config(page_title="Medical Report Generator", layout="centered")
st.title("🩺 Medical Report Generator with PDF")

# Hugging Face API key
HF_API_KEY = st.secrets["HF_API_KEY"]  # Add this in your .streamlit/secrets.toml

# Excel files to load
excel_files = [
    "Antibiotic_Tablets_Dataset (4).xlsx",
    "Anti_Diabetic_Drugs.xlsx",
    "Anti_Hypertensive_Drugs_Dataset_Full.xlsx",
    "Anti_neoplastic_Drugs_Dataset_Complete.xlsx",
    "Anti_Tubercular_Agents (1).xlsx",
]

# Load and combine Excel data
@st.cache_data
def load_combined_data():
    dfs = []
    for file in excel_files:
        if os.path.exists(file):
            df = pd.read_excel(file)
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

df = load_combined_data()

# UI Inputs
name = st.text_input("Patient Name")
age = st.number_input("Age", min_value=0, max_value=120)
mobile = st.text_input("Mobile Number")
query = st.text_input("Enter Disease or Medicine")

# Generate report using Hugging Face LLaMA 3
def generate_detailed_report_llama(name, age, mobile, disease, doctor_type, medicine, diet):
    try:
        prompt = (
            f"Create a professional and empathetic medical report for the following:\n\n"
            f"Patient Name: {name}\n"
            f"Age: {age}\n"
            f"Mobile: {mobile}\n"
            f"Diagnosed Disease: {disease}\n"
            f"Required Doctor Type: {doctor_type}\n"
            f"Prescribed Medicine: {medicine}\n"
            f"Dietary Advice: {diet}\n\n"
            f"Format the report into 4 paragraphs:\n"
            f"1. Patient's personal details.\n"
            f"2. Explanation of the disease.\n"
            f"3. Doctor and medication recommendation.\n"
            f"4. Dietary and lifestyle guidance."
        )

        url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": 0.7,
                "max_new_tokens": 600,
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()[0]["generated_text"]
    except Exception as e:
        return f"⚠️ Error generating report: {e}"

# Generate PDF using standard Arial (no DejaVu)
def generate_pdf(report_text, filename="medical_report.pdf"):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in report_text.split('\n'):
            pdf.multi_cell(0, 10, line)
        pdf.output(filename)
        return True
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return False

# Main logic
if st.button("Generate Report"):
    if name and mobile and query:
        filtered = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)]

        if not filtered.empty:
            record = filtered.iloc[0]
            disease = record.get("Disease", "an unspecified condition")
            doctor_type = record.get("Doctor Type", "a general physician")
            medicine = record.get("Medicine Name", "a prescribed medicine")
            diet = record.get("Diet Advice", "a general healthy diet")

            report = generate_detailed_report_llama(name, age, mobile, disease, doctor_type, medicine, diet)

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
