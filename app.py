import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import google.generativeai as genai

# Page configuration
st.set_page_config(page_title="Medical Report Generator", layout="centered")
st.title("🩺 Medical Report Generator with PDF")

# Load Gemini API key
GENAI_API_KEY = st.secrets["GENAI_API_KEY"]
genai.configure(api_key=GENAI_API_KEY)

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

# Generate report using Gemini
def generate_detailed_report_with_gemini(name, age, mobile, disease, doctor_type, medicine, diet):
    try:
        prompt = (
            "Create a professional and empathetic medical report for the following:\n\n"
            f"- Patient Name: {name}\n"
            f"- Age: {age}\n"
            f"- Mobile: {mobile}\n"
            f"- Diagnosed Disease: {disease}\n"
            f"- Required Doctor Type: {doctor_type}\n"
            f"- Prescribed Medicine: {medicine}\n"
            f"- Dietary Advice: {diet}\n\n"
            "Format the report into 4 paragraphs:\n"
            "1. Patient's personal details.\n"
            "2. Explanation of the disease.\n"
            "3. Doctor and medication recommendation.\n"
            "4. Dietary and lifestyle guidance."
        )

        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Error generating report: {e}"

# Generate PDF using FPDF
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

            report = generate_detailed_report_with_gemini(name, age, mobile, disease, doctor_type, medicine, diet)

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
