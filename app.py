import streamlit as st
import pandas as pd
from gtts import gTTS
from fpdf import FPDF

# Load Excel
@st.cache_data
def load_data():
    file_path = "/mnt/data/a5f9c644-a334-4ff7-af88-a17fb63922ba.xlsx"
    return pd.read_excel(file_path)

df = load_data()

# App UI
st.set_page_config(page_title="Medical Report Generator", layout="centered")
st.title("🩺 Medical Report Generator with Audio and PDF")

# Input fields
name = st.text_input("Patient Name")
age = st.number_input("Age", min_value=0, max_value=120)
mobile = st.text_input("Mobile Number")
query = st.text_input("Enter Disease or Medicine")
language = st.selectbox("Select language for audio", ["Tamil", "Hindi"])

lang_code_map = {
    "Tamil": "ta",
    "Hindi": "hi"
}

# Generate report
def generate_detailed_report(name, age, mobile, query, df):
    filtered = df[df.apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)]
    if filtered.empty:
        return None, None, "No relevant data found."

    record = filtered.iloc[0]
    disease = record.get('Disease', 'an unspecified condition')
    doctor_type = record.get('Doctor Type', 'a general physician')
    medicine = record.get('Medicine Name', 'a prescribed medicine')
    diet = record.get('Diet Advice', 'a general healthy diet')

    para1 = f"Patient Name: {name}, Age: {age}, Mobile: {mobile}."
    para2 = f"The patient appears to be diagnosed with {disease}. This condition requires appropriate medical attention."
    para3 = f"A consultation with a specialist in {doctor_type} is recommended. Suggested medicine: {medicine}."
    para4 = f"Dietary advice: {diet}. Regular exercise and lifestyle adjustments are encouraged."

    full_report = "\n\n".join([para1, para2, para3, para4])
    
    # TTS should ONLY say disease and medicine
    tts_text = f"{disease}. மருந்து: {medicine}." if lang_code_map[language] == "ta" else f"{disease}. दवा: {medicine}."

    return full_report, tts_text, None

# PDF Generation
def generate_pdf(report_text, filename="medical_report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in report_text.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)

# TTS Audio Generation
def generate_audio(text, lang_code, filename="audio.mp3"):
    tts = gTTS(text=text, lang=lang_code)
    tts.save(filename)

if st.button("Generate Report"):
    if name and mobile and query:
        report, tts_text, error = generate_detailed_report(name, age, mobile, query, df)

        if error:
            st.warning(error)
        else:
            st.markdown("## 📝 Medical Report")
            st.markdown(report)

            # PDF
            pdf_filename = "medical_report.pdf"
            generate_pdf(report, pdf_filename)
            with open(pdf_filename, "rb") as f:
                st.download_button("📥 Download PDF", f, file_name=pdf_filename)

            # TTS — use disease/medicine only
            audio_filename = "audio.mp3"
            generate_audio(tts_text, lang_code_map[language], audio_filename)
            st.audio(audio_filename)
    else:
        st.warning("Please fill all fields.")
