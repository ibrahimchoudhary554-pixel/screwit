import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import os

st.set_page_config(page_title="Data Bot", layout="centered")

# Initialize Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# --- THE FIX IS HERE ---
# We use gemini-1.5-flash which is the current standard.
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash') 
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
                    st.success("Access Granted! Loading Chat...")
                    st.rerun()
                else:
                    st.error(f"Wrong password.")
            else:
                st.error(f"User '{user_in}' not found.")
                
        except Exception as e:
            st.error(f"System Error: {e}")
    st.stop()

# --- CHAT INTERFACE ---
st.title("🤖 Chatbot Live")

if "history" not in st.session_state:
    st.session_state.history = []

# Display chat history
for m in st.session_state.history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ask me something..."):
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            # Generate the response
            res = model.generate_content(prompt)
            st.markdown(res.text)
            st.session_state.history.append({"role": "assistant", "content": res.text})
        except Exception as e:
            st.error(f"AI Error: {e}")
            st.info("If you see 'NotFound', try changing 'gemini-1.5-flash' to 'gemini-1.5-pro' in the code.")
