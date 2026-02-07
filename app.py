import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import os

st.set_page_config(page_title="Data Bot", layout="centered")

# Initialize Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Configure Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')

# Login Logic
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Login")
    user_in = st.text_input("User").strip()
    pass_in = st.text_input("Pass", type="password").strip()
    
    if st.button("Login"):
        try:
            # ttl=0 forces it to grab the newest data from your sheet
            df = conn.read(worksheet="Users", ttl=0)
            
            # FORCE HEADERS TO LOWERCASE (This fixes the 'Invalid Login' error)
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            # Clean the data rows
            df = df.astype(str).apply(lambda x: x.str.strip())
            
            # Check for match
            if ((df['username'] == user_in) & (df['password'] == pass_in)).any():
                st.session_state.auth = True
                st.success("Success! Redirecting...")
                st.rerun()
            else:
                st.error("Invalid Login. Check your Sheet headers are 'username' and 'password'")
        except Exception as e:
            st.error(f"Error: {e}")
    st.stop()

# Chat System
st.title("🤖 Chatbot Live")
if "history" not in st.session_state:
    st.session_state.history = []

for m in st.session_state.history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ask me something..."):
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        res = model.generate_content(prompt)
        st.markdown(res.text)
        st.session_state.history.append({"role": "assistant", "content": res.text})
