import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import os

st.set_page_config(page_title="Data Bot", layout="centered")

conn = st.connection("gsheets", type=GSheetsConnection)

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')

if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Login")
    user_in = st.text_input("User").strip()
    pass_in = st.text_input("Pass", type="password").strip()
    
    if st.button("Login"):
        try:
            # We add ttl=0 to force it to ignore old saved data
            df = conn.read(worksheet="Users", ttl=0)
            
            # DEBUG: This will show us exactly what the sheet headers look like
            # st.write("Debug - Sheet Columns:", df.columns.tolist())
            
            # Force everything to lowercase and remove spaces
            df.columns = [str(c).lower().strip() for c in df.columns]
            df = df.astype(str).apply(lambda x: x.str.strip().lower())
            
            # Match check
            match = df[(df['username'] == user_in.lower()) & (df['password'] == pass_in.lower())]
            
            if not match.empty:
                st.session_state.auth = True
                st.success("Success!")
                st.rerun()
            else:
                st.error("Invalid Login. I see these users in the sheet: " + str(df['username'].values))
        except Exception as e:
            st.error(f"Error: {e}")
    st.stop()

st.title("🤖 Chatbot Live")
if prompt := st.chat_input("Ask me something..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        res = model.generate_content(prompt)
        st.markdown(res.text)
