# resume_checker.py

import streamlit as st  # Streamlit for the web application framework
from utilities import load_text_from_file, calculate_match_score, generate_recommendations, create_pdf

# Main function to run the Streamlit app
def main():
    st.title("Resume and Job Description Checker")
    
    resume_files = st.file_uploader("Upload your resumes (PDF or TXT)", type=['pdf', 'txt'], accept_multiple_files=True)
    job_description_file = st.file_uploader("Upload the job description (PDF or TXT)", type=['pdf', 'txt'])

    job_description = ""
    
    if job_description_file is not None:
        job_description = load_text_from_file(job_description_file)

    if job_description:
        # Add a slider for setting the score threshold as a percentage (1 to 100)
        threshold_score = st.slider("Set a match score threshold (%):", min_value=1, max_value=100, value=40, step=1)

        for resume_file in resume_files:
            if resume_file is not None:
                resume = load_text_from_file(resume_file)
                st.subheader(f"Editing Resume: {resume_file.name}")
                
                edited_resume = st.text_area("Edit Your Resume:", resume, height=300, key=resume_file.name)

                score = calculate_match_score(edited_resume, job_description)
                st.progress(score)  # Change this to score since it is already in [0, 1]
                
                # Convert threshold score from percentage to a decimal for comparison
                threshold_score_decimal = threshold_score / 100.0

                # Display the scores in percentage format
                displayed_score = score * 100
                if displayed_score >= threshold_score:
                    st.success(f"Good match! Score: {displayed_score:.2f}%")
                else:
                    st.warning(f"Not a good match. Score is below the threshold of {threshold_score:.2f}%. Your score: {displayed_score:.2f}%")

                recommendations = generate_recommendations(edited_resume, job_description)
                recommendations_input = st.text_area("Recommendations to improve your resume:", recommendations, key=f"rec_{resume_file.name}")
                
                if st.button(f"Recalculate Match Score for {resume_file.name}"):
                    updated_resume = edited_resume + "\n" + recommendations_input
                    updated_score = calculate_match_score(updated_resume, job_description)
                    displayed_updated_score = updated_score * 100
                    st.metric(label="Updated Match Score", value=f"{displayed_updated_score:.2f}%")
                    st.progress(updated_score)  # This should reflect the original score (0 to 1)

                    # Use the converted threshold again
                    if updated_score >= threshold_score_decimal:
                        st.success(f"Good match! Score: {displayed_updated_score:.2f}%")

                        pdf_output = create_pdf(updated_resume)
                        original_filename = resume_file.name
                        if original_filename.lower().endswith('.pdf'):
                            original_filename = original_filename[:-4]

                        st.download_button("Download Updated Resume", data=pdf_output, 
                                           file_name=f'updated_{original_filename}.pdf', mime='application/pdf')
                    else:
                        st.warning(f"Not a good match. Score is below the threshold of {threshold_score:.2f}%. Your score: {displayed_updated_score:.2f}%")

# Entry point of the program when run directly
if __name__ == "__main__":
    main()