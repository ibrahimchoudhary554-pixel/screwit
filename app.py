import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os

# --- AUTH & CONFIG ---
st.set_page_config(page_title="Data-Fed Bot", layout="centered")

# 1. Initialize Google Sheets Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Configure Gemini AI
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Missing GEMINI_API_KEY in secrets!")

# --- DATA LOADING ---
def load_training_data(filepath="data.txt"):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return "No training data found in data.txt."

knowledge_base = load_training_data()

# --- LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Security Check")
    
    input_user = st.text_input("Username").strip()
    input_pw = st.text_input("Password", type="password").strip()
    
    if st.button("Enter the Matrix"):
        try:
            # We use st.secrets specifically to ensure the URL is pulled correctly
            sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
            
            # Read the 'Users' tab - this is where the capital 'Users' matters!
            df = conn.read(spreadsheet=sheet_url, worksheet="Users")
            
            # Check if dataframe is empty
            if df.empty:
                st.error("The 'Users' sheet is empty! Add a username/password to row 2.")
            else:
                # Clean data: Convert to string and remove hidden spaces
                df = df.astype(str).apply(lambda x: x.str.strip())
                
                # Verify column names exist
                if 'username' in df.columns and 'password' in df.columns:
                    user_match = (df['username'] == input_user) & (df['password'] == input_pw)
                    
                    if user_match.any():
                        st.session_state.logged_in = True
                        st.success("Access Granted!")
                        st.rerun()
                    else:
                        st.error("Access Denied. Check your spreadsheet row 2.")
                else:
                    st.error(f"Headers mismatch! Sheet headers are: {list(df.columns)}")
        except Exception as e:
            st.error(f"Login Error: {e}")
            st.info("Ensure tab name is 'Users' and the bot email has Editor access.")
    st.stop()

# --- CHAT INTERFACE ---
st.title("🤖 Your AI Puppet")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me something..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

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
            st.error(f"Gemini Error: {e}")
