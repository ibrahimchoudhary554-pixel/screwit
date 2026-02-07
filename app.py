import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import os

st.set_page_config(page_title="Data Bot", layout="centered")

# Initialize Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# --- THE FIX: ROBUST MODEL LOADING ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # We use 'gemini-1.5-flash-latest' to avoid the 404 version error
    model = genai.GenerativeModel('gemini-1.5-flash-latest') 
else:
    st.error("Check your Streamlit Secrets for GEMINI_API_KEY")

if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Login")
    user_in = st.text_input("User").strip()
    pass_in = st.text_input("Pass", type="password").strip()
    
    if st.button("Login"):
        try:
            df = conn.read(worksheet="Users", ttl=0)
            df.columns = [str(c).lower().strip() for c in df.columns]
            df = df.astype(str)
            for col in df.columns:
                df[col] = df[col].str.strip()

            user_found = df[df['username'] == user_in]
            
            if not user_found.empty:
                stored_password = str(user_found['password'].values[0])
                if stored_password == str(pass_in):
                    st.session_state.auth = True
                    st.success("Access Granted!")
                    st.rerun()
                else:
                    st.error("Wrong password.")
            else:
                st.error(f"User '{user_in}' not found.")
        except Exception as e:
            st.error(f"System Error: {e}")
    st.stop()

# --- CHAT INTERFACE ---
st.title("🤖 AI is Live")

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
            # We call the model here
            res = model.generate_content(prompt)
            st.markdown(res.text)
            st.session_state.history.append({"role": "assistant", "content": res.text})
        except Exception as e:
            # If it still fails, we try the older pro model as a backup
            try:
                backup_model = genai.GenerativeModel('gemini-pro')
                res = backup_model.generate_content(prompt)
                st.markdown(res.text)
                st.session_state.history.append({"role": "assistant", "content": res.text})
            except:
                st.error(f"AI Still Grumpy: {e}")
                st.info("Check Google AI Studio to see which models are enabled for your key.")
