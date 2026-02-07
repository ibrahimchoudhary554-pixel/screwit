import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import os

st.set_page_config(page_title="Data Bot", layout="centered")

# Initialize Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# --- THE FIX: GOING OLD SCHOOL ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # We are using 'gemini-pro' because your system is rejecting the 'flash' names
    model = genai.GenerativeModel('gemini-pro') 
else:
    st.error("Missing GEMINI_API_KEY in secrets!")

if 'auth' not in st.session_state:
    st.session_state.auth = False

# --- LOGIN ---
if not st.session_state.auth:
    st.title("🔒 Login")
    user_in = st.text_input("User").strip()
    pass_in = st.text_input("Pass", type="password").strip()
    
    if st.button("Login"):
        try:
            df = conn.read(worksheet="Users", ttl=0)
            df.columns = [str(c).lower().strip() for c in df.columns]
            df = df.astype(str).apply(lambda x: x.str.strip())

            user_found = df[df['username'] == user_in]
            if not user_found.empty:
                if str(user_found['password'].values[0]) == str(pass_in):
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Wrong password.")
            else:
                st.error("User not found.")
        except Exception as e:
            st.error(f"System Error: {e}")
    st.stop()

# --- CHAT ---
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
        try:
            # Simple call to the most compatible model
            res = model.generate_content(prompt)
            st.markdown(res.text)
            st.session_state.history.append({"role": "assistant", "content": res.text})
        except Exception as e:
            st.error(f"Google is being difficult: {e}")
            st.info("Try checking your API key status at aistudio.google.com")
