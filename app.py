import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import os

st.set_page_config(page_title="The Bot That Finally Works", layout="centered")

# Initialize Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# --- THE SMART MODEL PICKER ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # We try three different names in order of likelihood
    model_names = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
    model = None
    
    for name in model_names:
        try:
            test_model = genai.GenerativeModel(name)
            # We don't actually call the API yet, just assign the name
            model = test_model
            break
        except:
            continue
else:
    st.error("Add GEMINI_API_KEY to your Secrets!")

# --- LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Last Chance Login")
    u_in = st.text_input("User").strip()
    p_in = st.text_input("Pass", type="password").strip()
    
    if st.button("Login"):
        try:
            df = conn.read(worksheet="Users", ttl=0)
            df.columns = [str(c).lower().strip() for c in df.columns]
            df = df.astype(str).apply(lambda x: x.str.strip())

            user_row = df[df['username'] == u_in]
            if not user_row.empty and str(user_row['password'].values[0]) == p_in:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Invalid credentials.")
        except Exception as e:
            st.error(f"Sheet Error: {e}")
    st.stop()

# --- CHAT ---
st.title("🤖 Chatbot (Round 10?)")

if "history" not in st.session_state:
    st.session_state.history = []

for m in st.session_state.history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Say something..."):
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            # We use a standard generation call
            res = model.generate_content(prompt)
            st.markdown(res.text)
            st.session_state.history.append({"role": "assistant", "content": res.text})
        except Exception as e:
            st.error(f"AI Error: {e}")
            st.info("Check if your API Key is active at aistudio.google.com")
