import streamlit as st
import chardet
import fitz  # PyMuPDF
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

def load_text_from_file(uploaded_file):
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
    vectorizer = CountVectorizer().fit_transform([resume, job_description])
    vectors = vectorizer.toarray()
    cosine_similarity = vectors[0].dot(vectors[1]) / (np.linalg.norm(vectors[0]) * np.linalg.norm(vectors[1]))
    return cosine_similarity

def generate_recommendations(resume, job_description):
    resume_words = set(resume.lower().split())
    job_description_words = set(job_description.lower().split())
    
    missing_keywords = job_description_words - resume_words  # Keywords in JD not in Resume
    recommendations = []
    if missing_keywords:
        recommendations.append("Consider adding the following keywords to your resume: " + ", ".join(missing_keywords))

    if not recommendations:
        recommendations.append("Your resume covers all necessary keywords based on the job description.")
    
    return "\n".join(recommendations)

def create_pdf(content):
    # Create a BytesIO buffer to hold the PDF data
    pdf_output = io.BytesIO()
    c = canvas.Canvas(pdf_output, pagesize=letter)
    width, height = letter

    # Set the starting position for the text
    y_position = height - 40
    
    # Write the content to the PDF
    for line in content.splitlines():
        c.drawString(30, y_position, line)
        y_position -= 15  # Move down for the next line

        # If y_position goes below the page margin, create a new page
        if y_position < 40:
            c.showPage()
            y_position = height - 40
    
    c.save()
    pdf_output.seek(0)  # Move to the beginning of the BytesIO object
    return pdf_output

def main():
    st.title("Resume and Job Description Checker")
    
    # File uploader for multiple resumes
    resume_files = st.file_uploader("Upload your resumes (PDF or TXT)", type=['pdf', 'txt'], accept_multiple_files=True)
    
    # File uploader for the job description
    job_description_file = st.file_uploader("Upload the job description (PDF or TXT)", type=['pdf', 'txt'])
    
    job_description = ""
    
    # Read content if the job description file is uploaded
    if job_description_file is not None:
        job_description = load_text_from_file(job_description_file)

    if job_description:
        for resume_file in resume_files:
            if resume_file is not None:
                resume = load_text_from_file(resume_file)
                st.subheader(f"Editing Resume: {resume_file.name}")
                
                # Display editable resume content
                edited_resume = st.text_area("Edit Your Resume:", resume, height=300, key=resume_file.name)

                # Calculate match score
                score = calculate_match_score(edited_resume, job_description)
                st.progress(score / 1.0)  # Display progress bar (normalized)

                # Feedback based on the match score
                if score > 0.4:
                    st.success(f"Good match! Score: {score:.2f}")
                else:
                    st.warning(f"Not a good match. Score is below 0.4. Your score: {score:.2f}")
                
                # Generate recommendations
                recommendations = generate_recommendations(edited_resume, job_description)
                recommendations_input = st.text_area("Recommendations to improve your resume:", recommendations, key=f"rec_{resume_file.name}")
                
                # Allow the user to recalculate the score with updated recommendations
                if st.button(f"Recalculate Match Score for {resume_file.name}"):
                    updated_resume = edited_resume + "\n" + recommendations_input
                    updated_score = calculate_match_score(updated_resume, job_description)
                    st.metric(label="Updated Match Score", value=f"{updated_score:.2f}")
                    st.progress(updated_score / 1.0)  # Display updated progress bar
                    if updated_score > 0.4:
                        st.success(f"Good match! Score: {updated_score:.2f}")
                        
                        # Generate PDF and enable download
                        pdf_output = create_pdf(updated_resume)
                        
                        # Ensure the original resume filename does not have .pdf extension if you're adding it again
                        original_filename = resume_file.name
                        if original_filename.lower().endswith('.pdf'):
                            original_filename = original_filename[:-4]  # Remove last 4 characters for .pdf

                        st.download_button("Download Updated Resume", data=pdf_output, 
                                           file_name=f'updated_{original_filename}.pdf', mime='application/pdf')
                    else:
                        st.warning(f"Not a good match. Score is below 0.4. Your score: {updated_score:.2f}")

if __name__ == "__main__":
    main()
