import streamlit as st
import pandas as pd
from fpdf import FPDF
import os

# Streamlit page config
st.set_page_config(page_title="Medical Report Generator", layout="centered")
st.title("🩺 Medical Report Generator with PDF Export")

# Define file names
excel_files = [
    "Antibiotic_Tablets_Dataset (4).xlsx",
    "Anti_Diabetic_Drugs.xlsx",
    "Anti_Hypertensive_Drugs_Dataset_Full.xlsx",
    "Anti_neoplastic_Drugs_Dataset_Complete.xlsx",
    "Anti_Tubercular_Agents (1).xlsx",
]

# Load and combine all Excel files
@st.cache_data
def load_combined_data():
    dfs = []
    for file in excel_files:
        if os.path.exists(file):
            df = pd.read_excel(file)
            dfs.append(df)
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame()

df = load_combined_data()

# Input fields
name = st.text_input("Patient Name")
age = st.number_input("Age", min_value=0, max_value=120)
mobile = st.text_input("Mobile Number")
query = st.text_input("Enter Disease or Medicine")

# Generate report
def generate_detailed_report(name, age, mobile, query, df):
    filtered = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)]
    if filtered.empty:
        return None

    record = filtered.iloc[0]
    disease = record.get('Disease', 'an unspecified condition')
    doctor_type = record.get('Doctor Type', 'a general physician')
    medicine = record.get('Medicine Name', 'a prescribed medicine')
    diet = record.get('Diet Advice', 'a general healthy diet')

    para1 = f"Patient Name: {name}, Age: {age}, Mobile: {mobile}."
    para2 = f"The patient has been diagnosed with {disease}. This condition may present symptoms requiring close observation and treatment."
    para3 = f"It is recommended to consult a doctor who specializes in {doctor_type}. The prescribed medication for this condition is {medicine}. Ensure to follow the dosage and frequency advised by your doctor."
    para4 = f"Dietary recommendations for this condition include: {diet}. Maintaining a balanced diet, avoiding allergens, and staying hydrated are key to recovery."

    return "\n\n".join([para1, para2, para3, para4])

# PDF Generation
def generate_pdf(report_text, filename="medical_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in report_text.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)

# Main button logic
if st.button("Generate Report"):
    if name and mobile and query:
        report = generate_detailed_report(name, age, mobile, query, df)
        if report:
            st.markdown("## 📝 Medical Report")
            st.markdown(report)

            # PDF generation
            pdf_filename = "medical_report.pdf"
            generate_pdf(report, pdf_filename)
            with open(pdf_filename, "rb") as f:
                st.download_button("📥 Download PDF", f, file_name=pdf_filename)

        else:
            st.warning("No relevant data found for the query.")
    else:
        st.warning("Please fill all fields.")
