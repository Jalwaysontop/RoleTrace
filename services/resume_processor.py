import pdfplumber
import re

# ---------------------------
# Extract text from resume
# ---------------------------
def extract_resume_text(file_path):
    text = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "

    return text.strip()


# ---------------------------
# Clean text
# ---------------------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ---------------------------
# Full pipeline
# ---------------------------
def process_resume(file_path):
    raw_text = extract_resume_text(file_path)
    cleaned_text = clean_text(raw_text)

    return {
        "raw_text": raw_text,
        "cleaned_text": cleaned_text
    }