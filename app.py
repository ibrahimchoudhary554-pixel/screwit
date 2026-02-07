import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os

# --- AUTH & CONFIG ---
st.set_page_config(page_title="Data-Fed Bot", layout="centered")

# 1. Initialize Google Sheets Connection
# Ensure your Secrets have [connections.gsheets] correctly set up!
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Configure Gemini AI
# Make sure GEMINI_API_KEY is in your Secrets!
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- DATA LOADING ---
def load_training_data(filepath="data.txt"):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return "No training data found in data.txt. Feed me some knowledge!"

knowledge_base = load_training_data()

# --- LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Security Check")
    
    # Use lowercase labels to match your spreadsheet headers in the screenshot
    # Change line 36 to this:
df = conn.read(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], worksheet="Users")
    input_pw = st.text_input("Password", type="password")
    
    if st.button("Enter the Matrix"):
        try:
            # Read the 'Users' tab
            df = conn.read(worksheet="Users")
            
            # Clean data: Convert everything to string and strip spaces
            df = df.astype(str).apply(lambda x: x.str.strip())
            
            # Check if the credentials exist in the sheet
            # Matches 'username' and 'password' headers exactly as seen in your screenshot
            user_match = (df['username'] == input_user) & (df['password'] == input_pw)
            
            if user_match.any():
                st.session_state.logged_in = True
                st.success("Access Granted! Welcome back.")
                st.rerun()
            else:
                st.error("Access Denied. That's not in the spreadsheet.")
        except Exception as e:
            st.error(f"Spreadsheet Error: {e}. Check if tab name is 'Users' and shared with the bot email.")
    st.stop()

# --- CHAT INTERFACE ---
st.title("🤖 Your AI Puppet")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask me something..."):
    # Add user message to UI and history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Combine file content (training data) with the user question
    full_prompt = (
        f"Context from data.txt:\n{knowledge_base}\n\n"
        f"User Question: {prompt}"
    )
    
    with st.chat_message("assistant"):
        try:
            response = model.generate_content(full_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Gemini had a stroke: {e}")

