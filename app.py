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

if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Login")
    # Using .strip() to remove any accidental spaces you might type
    user_in = st.text_input("User").strip()
    pass_in = st.text_input("Pass", type="password").strip()
    
    if st.button("Login"):
        try:
            # Force refresh from Google Sheets
            df = conn.read(worksheet="Users", ttl=0)
            
            # 1. Clean Headers
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            # 2. Clean Data (The Nuclear Option)
            # This turns everything into a plain string and removes invisible spaces
            df = df.astype(str)
            for col in df.columns:
                df[col] = df[col].str.strip()

            # 3. Search for the user
            user_found = df[df['username'] == user_in]
            
            if not user_found.empty:
                # 4. Compare Passwords
                # We convert both to strings just to be 100% sure
                stored_password = str(user_found['password'].values[0])
                if stored_password == str(pass_in):
                    st.session_state.auth = True
                    st.success("Access Granted! Loading Chat...")
                    st.rerun()
                else:
                    st.error(f"Wrong password. The sheet has '{stored_password}' but you typed '{pass_in}'")
            else:
                st.error(f"User '{user_in}' not found. Check your sheet Column A.")
                
        except Exception as e:
            st.error(f"System Error: {e}")
    st.stop()

# --- CHAT INTERFACE ---
st.title("🤖 Chatbot Live")
if prompt := st.chat_input("Ask me something..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        res = model.generate_content(prompt)
        st.markdown(res.text)
