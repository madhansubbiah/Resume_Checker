# utilities.py

import chardet          # chardet for character encoding detection
import fitz             # PyMuPDF for PDF processing
import numpy as np      # NumPy for numerical computations
from sklearn.feature_extraction.text import CountVectorizer  # For converting text to vectors
import io               # For handling byte I/O
from reportlab.lib.pagesizes import letter  # For PDF page size
from reportlab.pdfgen import canvas  # For generating PDFs

def load_text_from_file(uploaded_file):
    """Load text from an uploaded file."""
    if uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            text = ""
            for page in pdf_document:
                text += page.get_text()
            pdf_document.close()
            return text
        else:
            raw_data = uploaded_file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            return raw_data.decode(encoding)
    return ""

def calculate_match_score(resume, job_description):
    """Calculate match score between a resume and job description."""
    vectorizer = CountVectorizer().fit_transform([resume, job_description])
    vectors = vectorizer.toarray()
    cosine_similarity = vectors[0].dot(vectors[1]) / (np.linalg.norm(vectors[0]) * np.linalg.norm(vectors[1]))
    return cosine_similarity

def generate_recommendations(resume, job_description):
    """Generate recommendations for improving a resume."""
    resume_words = set(resume.lower().split())
    job_description_words = set(job_description.lower().split())
    missing_keywords = job_description_words - resume_words
    recommendations = []
    if missing_keywords:
        recommendations.append("Consider adding the following keywords to your resume: " + ", ".join(missing_keywords))
    if not recommendations:
        recommendations.append("Your resume covers all necessary keywords based on the job description.")
    return "\n".join(recommendations)

def create_pdf(content):
    """Create a PDF with given content."""
    pdf_output = io.BytesIO()
    c = canvas.Canvas(pdf_output, pagesize=letter)
    width, height = letter
    y_position = height - 40
    
    for line in content.splitlines():
        c.drawString(30, y_position, line)
        y_position -= 15
        if y_position < 40:
            c.showPage()
            y_position = height - 40
    
    c.save()
    pdf_output.seek(0)
    return pdf_output
