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

# Load Knowledge Base
def get_data():
    if os.path.exists("data.txt"):
        with open("data.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "No context available."

kb = get_data()

# Login Logic
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Login")
    user_in = st.text_input("User").strip()
    pass_in = st.text_input("Pass", type="password").strip()
    
    if st.button("Login"):
        try:
            # ttl=0 ensures it doesn't remember the old 'Response 200' error
            df = conn.read(worksheet="Users", ttl=0)
            df = df.astype(str).apply(lambda x: x.str.strip())
            
            # Check against lowercase headers from your screenshot
            if ((df['username'] == user_in) & (df['password'] == pass_in)).any():
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Invalid Login")
        except Exception as e:
            st.error(f"Error: {e}")
    st.stop()

# Chat System
st.title("🤖 Chat with your Data")
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
        res = model.generate_content(f"Context: {kb}\n\nQuestion: {prompt}")
        st.markdown(res.text)
        st.session_state.history.append({"role": "assistant", "content": res.text})
