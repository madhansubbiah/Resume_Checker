# Import necessary libraries
import streamlit as st  # Streamlit for web application framework
import chardet          # chardet for character encoding detection
import fitz             # PyMuPDF for PDF processing
import numpy as np      # NumPy for numerical computations
from sklearn.feature_extraction.text import CountVectorizer  # For converting text to vectors
from reportlab.lib.pagesizes import letter  # For PDF page size
from reportlab.pdfgen import canvas  # For generating PDFs
import io               # For handling byte I/O

# Function to load text from an uploaded file
def load_text_from_file(uploaded_file):
    # Check if a file was uploaded
    if uploaded_file is not None:
        # Check if the uploaded file is a PDF
        if uploaded_file.type == "application/pdf":
            # Open the PDF document and read its content
            pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            text = ""
            # Loop through each page in the PDF
            for page in pdf_document:
                text += page.get_text()  # Extract text from the page
            pdf_document.close()  # Close the document
            return text  # Return the extracted text
        else:
            # For non-PDF files, read raw data
            raw_data = uploaded_file.read()
            # Detect the character encoding of the raw data
            result = chardet.detect(raw_data)
            encoding = result['encoding']  # Get the detected encoding
            return raw_data.decode(encoding)  # Decode and return the text
    return ""  # Return an empty string if no file was uploaded

# Function to calculate match score between a resume and job description
def calculate_match_score(resume, job_description):
    # Create a CountVectorizer and fit it to the resume and job description
    vectorizer = CountVectorizer().fit_transform([resume, job_description])
    vectors = vectorizer.toarray()  # Convert to arrays for cosine similarity calculation
    # Calculate cosine similarity between the two vectors
    cosine_similarity = vectors[0].dot(vectors[1]) / (np.linalg.norm(vectors[0]) * np.linalg.norm(vectors[1]))
    return cosine_similarity  # Return the calculated similarity score

# Function to generate recommendations for improving a resume
def generate_recommendations(resume, job_description):
    # Split the resume and job description into sets of lowercase words
    resume_words = set(resume.lower().split())
    job_description_words = set(job_description.lower().split())
    
    # Determine missing keywords that are in the job description but not in the resume
    missing_keywords = job_description_words - resume_words  
    recommendations = []
    # If there are missing keywords, suggest them for addition to the resume
    if missing_keywords:
        recommendations.append("Consider adding the following keywords to your resume: " + ", ".join(missing_keywords))

    # If no keywords are missing, indicate that the resume is complete
    if not recommendations:
        recommendations.append("Your resume covers all necessary keywords based on the job description.")
    
    return "\n".join(recommendations)  # Return the recommendations as a single string

# Function to create a PDF with given content
def create_pdf(content):
    # Create a BytesIO buffer to hold the PDF data
    pdf_output = io.BytesIO()
    c = canvas.Canvas(pdf_output, pagesize=letter)  # Create a canvas for the PDF
    width, height = letter  # Get the width and height of the page

    # Set the starting position for the text
    y_position = height - 40
    
    # Write the content to the PDF
    for line in content.splitlines():  # For each line in the content
        c.drawString(30, y_position, line)  # Draw the line at the specified position
        y_position -= 15  # Move down for the next line

        # If y_position goes below the page margin, create a new page
        if y_position < 40:
            c.showPage()  # Start a new page
            y_position = height - 40  # Reset the position for the new page
    
    c.save()  # Save the PDF
    pdf_output.seek(0)  # Move to the beginning of the BytesIO object
    return pdf_output  # Return the PDF output

# Main function to run the Streamlit app
def main():
    st.title("Resume and Job Description Checker")  # Set the title of the app
    
    # File uploader for multiple resumes (PDF or TXT)
    resume_files = st.file_uploader("Upload your resumes (PDF or TXT)", type=['pdf', 'txt'], accept_multiple_files=True)
    
    # File uploader for the job description
    job_description_file = st.file_uploader("Upload the job description (PDF or TXT)", type=['pdf', 'txt'])
    
    job_description = ""  # Initialize variable for job description text
    
    # Read content if the job description file is uploaded
    if job_description_file is not None:
        job_description = load_text_from_file(job_description_file)  # Load the job description text

    # If there is a job description loaded, process each uploaded resume
    if job_description:
        for resume_file in resume_files:
            if resume_file is not None:
                resume = load_text_from_file(resume_file)  # Load the resume text
                st.subheader(f"Editing Resume: {resume_file.name}")  # Display the resume name
                
                # Display editable resume content in a text area
                edited_resume = st.text_area("Edit Your Resume:", resume, height=300, key=resume_file.name)

                # Calculate match score between the edited resume and job description
                score = calculate_match_score(edited_resume, job_description)
                st.progress(score / 1.0)  # Display progress bar based on score (normalized)

                # Provide feedback based on the match score
                if score > 0.4:
                    st.success(f"Good match! Score: {score:.2f}")  # If score is good, show success message
                else:
                    st.warning(f"Not a good match. Score is below 0.4. Your score: {score:.2f}")  # If score is poor, show warning
                
                # Generate recommendations for resume improvement
                recommendations = generate_recommendations(edited_resume, job_description)
                recommendations_input = st.text_area("Recommendations to improve your resume:", recommendations, key=f"rec_{resume_file.name}")
                
                # Allow the user to recalculate the score with updated recommendations
                if st.button(f"Recalculate Match Score for {resume_file.name}"):
                    updated_resume = edited_resume + "\n" + recommendations_input  # Combine edited resume and recommendations
                    updated_score = calculate_match_score(updated_resume, job_description)  # Calculate updated score
                    st.metric(label="Updated Match Score", value=f"{updated_score:.2f}")  # Display updated score
                    st.progress(updated_score / 1.0)  # Display updated progress bar
                    if updated_score > 0.4:
                        st.success(f"Good match! Score: {updated_score:.2f}")  # If updated score is good, show success
                        
                        # Generate PDF of the updated resume and prepare for download
                        pdf_output = create_pdf(updated_resume)
                        
                        # Ensure the original resume filename does not have a .pdf extension if you are adding it again
                        original_filename = resume_file.name
                        if original_filename.lower().endswith('.pdf'):
                            original_filename = original_filename[:-4]  # Remove last 4 characters for .pdf

                        # Create a download button for the updated resume PDF
                        st.download_button("Download Updated Resume", data=pdf_output, 
                                           file_name=f'updated_{original_filename}.pdf', mime='application/pdf')
                    else:
                        st.warning(f"Not a good match. Score is below 0.4. Your score: {updated_score:.2f}")  # Show warning for poor updated score

# Entry point of the program when run directly
if __name__ == "__main__":
    main()  # Call the main function to execute the application
