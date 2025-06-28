import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import google.generativeai as genai
from gtts import gTTS

# Page setup
st.set_page_config(page_title="Medical Report Generator", layout="centered")
st.title("🩺 Medical Report Generator with PDF and TTS")

# Set your Gemini API key here (make sure to keep it secure in production)
GENAI_API_KEY = st.secrets["AIzaSyBGOXlvs7zKepT18xKJPwwq4KpChFAugMA"]
genai.configure(api_key=GENAI_API_KEY)

# Define Excel file paths
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
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

df = load_combined_data()

# UI Inputs
name = st.text_input("Patient Name")
age = st.number_input("Age", min_value=0, max_value=120)
mobile = st.text_input("Mobile Number")
query = st.text_input("Enter Disease or Medicine")
language = st.selectbox("Select language for audio", ["Tamil", "Hindi"])

lang_code_map = {
    "Tamil": "ta",
    "Hindi": "hi"
}

# Generate report using Gemini
@st.cache_data(show_spinner=False)
def generate_detailed_report_with_gemini(name, age, mobile, disease, doctor_type, medicine, diet):
    prompt = f"""
    Create a professional and empathetic medical report for the following:
    
    - Patient Name: {name}
    - Age: {age}
    - Mobile: {mobile}
    - Diagnosed Disease: {disease}
    - Required Doctor Type: {doctor_type}
    - Prescribed Medicine: {medicine}
    - Dietary Advice: {diet}
    
    Format the report into 4 detailed paragraphs:
    1. Patient's personal information.
    2. Description of the disease.
    3. Consultation and medication details.
    4. Dietary and lifestyle recommendations.
    """
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.text.strip()

# PDF generation
def generate_pdf(report_text, filename="medical_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in report_text.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)

# TTS for disease and medicine
def generate_tts(text, lang_code, filename="audio.mp3"):
    tts = gTTS(text=text, lang=lang_code)
    tts.save(filename)

# Generate Report Button
if st.button("Generate Report"):
    if name and mobile and query:
        filtered = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)]
        if not filtered.empty:
            record = filtered.iloc[0]
            disease = record.get('Disease', 'an unspecified condition')
            doctor_type = record.get('Doctor Type', 'a general physician')
            medicine = record.get('Medicine Name', 'a prescribed medicine')
            diet = record.get('Diet Advice', 'a general healthy diet')

            report = generate_detailed_report_with_gemini(name, age, mobile, disease, doctor_type, medicine, diet)

            st.markdown("## 📝 Medical Report")
            st.markdown(report)

            # Downloadable PDF
            pdf_filename = "medical_report.pdf"
            generate_pdf(report, pdf_filename)
            with open(pdf_filename, "rb") as f:
                st.download_button("📥 Download PDF", f, file_name=pdf_filename)

            # Generate audio for disease and medicine
            tts_text = f"Disease: {disease}. Medicine: {medicine}."
            audio_file = "audio.mp3"
            generate_tts(tts_text, lang_code_map[language], audio_file)
            st.audio(audio_file)

        else:
            st.warning("No relevant data found for the query.")
    else:
        st.warning("Please fill all fields.")
