#from langchain_huggingface import ChatHuggingFace,HuggingFaceEndpoint
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from googletrans import Translator
import streamlit as st
import os
import requests
import base64

#load environment
load_dotenv()

#Page setup
st.set_page_config(page_title="AI Text Summarizer",page_icon="🧠", layout="wide")
translator=Translator()

#Theme toggle
dark_mode=st.toggle("🌗 Dark Mode")
#bg_color="#1e1e1e" if dark_mode else "#f4f6f7"
#text_color="#ffffff" if dark_mode else "#000000"

bg_color = "#1e1e1e" if dark_mode else "#ffffff"
text_color = "#ffffff" if dark_mode else "#000000"
box_bg_color = "#333333" if dark_mode else "#dff9fb"
box_text_color = "#ffffff" if dark_mode else "#000000"

st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <style>
        html, body, [class*="css"]  {
            background-color: %s !important;
            color: %s !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .title-box {
            background-color: #4b7bec;
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        .summary-box {
            background-color: %s;
            border-left: 5px solid #4b7bec;
            padding: 1rem;
            border-radius: 10px;
            margin-top: 1rem;
            font-size: 1.1rem;
            color: %s;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }
        .form-control, .form-select {
            margin-bottom: 1rem;
        }
        .btn-custom {
            background-color: #4b7bec;
            border: none;
            color: white;
        }
        .btn-custom:hover {
            background-color: #3867d6;
        }
        .footer {
            text-align: center;
            margin-top: 3rem;
            padding: 1rem;
            color: %s;
            font-size: 0.9rem;
            border-top: 1px solid #ccc;
        }
    </style>
""" % (bg_color, text_color, box_bg_color, box_text_color, text_color), unsafe_allow_html=True)
st.markdown('<div class="title-box animate__animated animate__fadeInDown"><h1>🧠 AI Text Summarizer</h1><p>Summarize, Translate, Upload and Chat your documents.</p></div>', unsafe_allow_html=True)

#Session state for login/logout
if "logged_in" not in st.session_state:
    st.session_state.logged_in=False

if "api_token" not in st.session_state:
    st.session_state.api_token=""
    

#Logout functionality
if st.session_state.logged_in:
    if st.button("🔒 Log Out"):
        st.session_state.logged_in=False
        st.session_state.api_token=""
        st.session_state.chat_history=[]
        st.success("You have been logged out.")
        st.stop()  

if not st.session_state.logged_in:
    api_token_input=st.text_input("🔐 Enter your Hugging Face API Token to login",type="password")
    if st.button("🔓 Log In",type="primary"):
        if api_token_input:
            st.session_state.logged_in=True
            st.session_state.api_token=api_token_input
            st.success("Logged in successfully !")
            st.rerun()
        else:
            st.warning("⚠️ Please enter a valid Hugging Face API token.")
    st.stop()

api_token=st.session_state.api_token
        
            

model_options={
    "facebook/bart-large-cnn":"facebook/bart-large-cnn",
    "google/pegasus-xsum":"google/pegasus-xsum",
    "Falconsai/text_summarization": "Falconsai/text_summarization"
}

selected_model=st.selectbox("🤖 Choose a summarization model",list(model_options.keys()))

lang_choices=['en','hi','es','fr','de','bn','gu']
selected_lang=st.selectbox("🌐 Translate Summary to",lang_choices)


#file upload
uploaded_file=st.file_uploader("📂 Upload a .txt or .pdf file",type=["txt","pdf"])
user_input=""

if uploaded_file:
    if uploaded_file.name.endswith(".txt"):
        user_input=uploaded_file.read().decode("utf-8")
    elif uploaded_file.name.endswith(".pdf"):
        reader=PdfReader(uploaded_file)
        extracted = [page.extract_text() for page in reader.pages if page.extract_text()]
        user_input = " ".join(extracted).strip()
        if not user_input:
            st.warning("⚠️ Could not extract text from this PDF. Please upload a text-based PDF.")
            st.stop()
    
    if st.button("❌ Remove Uploaded File"):
        uploaded_file=None
        user_input=""
        st.success("Uploaded file removed.")
chat_history=st.session_state.get("chat_history",[])    

if not uploaded_file:
    user_input=st.text_area("💬 Enter your text to summarize or chat with:",height=200)

if st.button("📝 Generate Summary",type="primary"):
    if not api_token:
         st.warning("⚠️ Please enter your Hugging Face API token.")
    elif not user_input.strip():
        st.warning("⚠️ Please enter or upload some text.")
    
    else:
        headers = {"Authorization": f"Bearer {api_token}"}
        api_url=f"https://api-inference.huggingface.co/models/{selected_model}"
        with st.spinner("Summarizing..."):
            try:
                payload={"inputs":user_input}
                response=requests.post(api_url,headers=headers,json=payload,timeout=60)
                response.raise_for_status()
                summary=response.json()[0]["summary_text"]
                st.markdown(f'<div class="summary-box animate__animated animate__fadeInUp">{summary}</div>', unsafe_allow_html=True)
                
                #Add  to chat history
                chat_history.append((user_input,summary))
                st.session_state.chat_history=chat_history
                
                #Word Count
                st.markdown(f"📏 **Summary Word Count:** `{len(summary.split())}` words")
                
                #Translation
                translated_summary=translator.translate(summary,dest=selected_lang).text
                st.markdown(f"🌍 **Translated Summary ({selected_lang}):**")
                st.success(translated_summary)
                #Download
                st.download_button("💾 Download Summary", summary, file_name="summary.txt")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


#chat history display and delete
if st.session_state.logged_in and chat_history:
    st.markdown("### 💬 Chat History")
    for i, (q,a) in enumerate(reversed(chat_history[-5:]),1):
        st.markdown(f"**User:**{q}")
        st.markdown(f"**AI:**{a}")
        
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history=[]
        st.success("Chat history cleared.")
              
# Footer
# st.markdown("""
#     <div class='footer'>
#       <p>Copyright  © 2025 AI Text Summarizer | Brijkishor Soni</p>
#     </div>
# """, unsafe_allow_html=True)