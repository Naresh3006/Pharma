import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import requests
import re

# Page config
st.set_page_config(page_title="Medical Report Generator", layout="centered")
st.title("🩺 Medical Report Generator with PDF")

# OpenRouter API setup
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
LLM_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

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

def generate_report(name, age, mobile, disease, doctor_type, medicine, diet):
    system_msg = {"role": "system", "content": "You are a medical assistant."}
    user_msg = {
        "role": "user",
        "content": (
            f"Generate a 4‑paragraph medical report:\n"
            f"1. Patient info: {name}, {age}, {mobile}\n"
            f"2. About the disease: {disease}\n"
            f"3. Doctor & medicine: {doctor_type}, {medicine}\n"
            f"4. Dietary advice: {diet}"
        )
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "meta-llama/llama-3.2-3b-instruct:free",
        "messages": [system_msg, user_msg],
        "max_tokens": 512,
        "temperature": 0.7
    }
    r = requests.post(LLM_ENDPOINT, headers=headers, json=payload)
    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"].strip()
    else:
        return f"⚠️ Error: {r.status_code} – {r.text}"

def generate_pdf(report, filename="medical_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    text = re.sub(r"[^\x00-\x7F]+", "", report)
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)

# Generate button logic
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
