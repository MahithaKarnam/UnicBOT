import streamlit as st
import requests
import os
import string
import PyPDF2

# Constants
OLLAMA_BASE_URL = "http://localhost:11434/v1"
MODEL_NAME = "llama3.2"

# Function to interact with Ollama's API (LLaMA-based)
def call_llama_api(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,  
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(f"{OLLAMA_BASE_URL}/chat/completions", json=data, headers=headers)
        response.raise_for_status()
        return response.json().get('choices', [{}])[0].get('message', {}).get('content', "No response from model.")
    except requests.exceptions.RequestException as e:
        return f"API error: {str(e)}"

# Load keywords from a text file into a set for quick lookup
def load_keywords(filename: str) -> set[str]:
    keywords = set()
    try:
        with open(filename, 'r') as file:
            for line in file:
                keywords.update(keyword.strip().lower() for keyword in line.split(',') if keyword.strip())
    except FileNotFoundError:
        st.error(f"Keyword file not found: {filename}")
    return keywords

# Clean user input by removing punctuation and converting to lowercase
def clean_input(user_input: str) -> str:
    return user_input.translate(str.maketrans('', '', string.punctuation)).lower()

# Improved keyword matching using partial and substring matching
def is_keyword_match(user_input: str, keywords: set[str]) -> bool:
    clean_input_text = clean_input(user_input)
    return any(keyword in clean_input_text for keyword in keywords)

# Check if the input contains greeting keywords
def is_greeting_query(user_input: str, greeting_keywords: set[str]) -> bool:
    return is_keyword_match(user_input, greeting_keywords)

# Check if the input contains exit keywords
def is_exit_query(user_input: str, exit_keywords: set[str]) -> bool:
    return is_keyword_match(user_input, exit_keywords)

# Check if the input contains any STEM-related keywords
def is_stem_query(user_input: str, stem_keywords: set[str]) -> bool:
    return is_keyword_match(user_input, stem_keywords)

# Check if the input contains appointment-related keywords
def is_appointment_query(user_input: str, appointment_keywords: set[str]) -> bool:
    return is_keyword_match(user_input, appointment_keywords)

# Check if the input contains rescheduling keywords
def is_reschedule_query(user_input: str, reschedule_keywords: set[str]) -> bool:
    return is_keyword_match(user_input, reschedule_keywords)

# Extract text from a PDF file using PyPDF2
def extract_pdf_text(file) -> str:
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page_num in range(len(reader.pages)):
        text += reader.pages[page_num].extract_text()
    return text

# Summarize content using LLaMA API instead of manual summary
def generate_summary_with_model(content: str) -> str:
    # Sending the extracted text to the LLaMA model to generate a summary
    prompt = f"Please provide a summary for the following content:\n\n{content}"
    return call_llama_api(prompt)

# Handle file upload (PDF or TXT)
def handle_file_upload(uploaded_file) -> str:
    if uploaded_file.type == "application/pdf":
        text = extract_pdf_text(uploaded_file)
    elif uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8")
    else:
        return "Unsupported file type. Please upload a PDF or text file."
    
    # Send the extracted content to the model to get a meaningful summary
    return generate_summary_with_model(text)

# Main chatbot function for STEM queries
def stem_chatbot(user_input: str, stem_keywords: set[str], greeting_keywords: set[str], exit_keywords: set[str], appointment_keywords: set[str], reschedule_keywords: set[str]) -> str:
    # Check for different types of queries in the prioritized order
    
    if is_greeting_query(user_input, greeting_keywords):
        return "Hello! How can I assist you today?"
    
    if is_reschedule_query(user_input, reschedule_keywords):
        return (
            "To make changes to your appointment, please reach out directly by emailing or calling our team:\n\n"
            "Email: info@unicgate.org\n\n"
            "Phone: +1 346-471-4390\n\n"
            "Please note that response times may vary as our team processes requests. We appreciate your patience and will do our best to accommodate your scheduling needs."
        )

    if is_appointment_query(user_input, appointment_keywords):
        return "You can check my available slots and schedule an appointment using this link: [Schedule Appointment](https://cal.com/tankyash1)"
    
    if is_stem_query(user_input, stem_keywords):
        return call_llama_api(user_input)

    if is_exit_query(user_input, exit_keywords):
        return "Goodbye! See you next time."

    # Fallback message for unrecognized input
    return "Sorry, I can only answer STEM-related questions or assist with appointment scheduling. Please ask something related to science, technology, engineering, or mathematics, or provide scheduling-related details."

def main():
    st.title("UNICBot 🤖")
    
    # Initialize session state variables
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'session_ended' not in st.session_state:
        st.session_state.session_ended = False

    # Load keywords once
    stem_keywords = load_keywords('/Users/yashtank/Desktop/Project 3/Code/stem_keywords.txt')
    greeting_keywords = load_keywords('/Users/yashtank/Desktop/Project 3/Code/greeting_keywords.txt')
    exit_keywords = load_keywords('/Users/yashtank/Desktop/Project 3/Code/exit_keywords.txt')
    appointment_keywords = load_keywords('/Users/yashtank/Desktop/Project 3/Code/appointment_keywords.txt')
    reschedule_keywords = load_keywords('/Users/yashtank/Desktop/Project 3/Code/reschedule_keywords.txt')

    # Display chat history
    st.subheader("Chat History")
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["message"])

    # Input form (always at the bottom)
    with st.form(key="input_form"):
        user_input = st.text_input("Enter your STEM-related question or attach a document...", "")
        uploaded_file = st.file_uploader("Attach a document", type=["pdf", "txt"], label_visibility="collapsed")
        submit_button = st.form_submit_button("Submit")

    if submit_button:
        if uploaded_file:
            # Handle file upload and display summarized content
            file_summary = handle_file_upload(uploaded_file)
            st.session_state.chat_history.append({"role": "user", "message": f"Uploaded file: {uploaded_file.name}"})
            st.session_state.chat_history.append({"role": "bot", "message": file_summary})
        elif user_input:
            # Process user question
            st.session_state.chat_history.append({"role": "user", "message": user_input})
            bot_response = stem_chatbot(user_input, stem_keywords, greeting_keywords, exit_keywords, appointment_keywords, reschedule_keywords)
            st.session_state.chat_history.append({"role": "bot", "message": bot_response})

# Call the main function
if __name__ == "__main__":
    main()
