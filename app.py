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
    user_in = st.text_input("User").strip()
    pass_in = st.text_input("Pass", type="password").strip()
    
    if st.button("Login"):
        try:
            # ttl=0 forces a fresh look at your Google Sheet
            df = conn.read(worksheet="Users", ttl=0)
            
            # Clean headers: remove spaces and make lowercase
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            # Clean data: Convert to string and remove spaces
            df = df.astype(str).apply(lambda x: x.str.strip())

            # DEBUG: Uncomment the line below if you want to see the table on screen
            # st.write("What the bot sees:", df)
            
            # Improved matching logic
            user_found = df[df['username'] == user_in]
            if not user_found.empty:
                # Check if password matches in that row
                if (user_found['password'] == pass_in).any():
                    st.session_state.auth = True
                    st.success("Success!")
                    st.rerun()
                else:
                    st.error("Wrong password.")
            else:
                st.error(f"User '{user_in}' not found in sheet.")
                
        except Exception as e:
            st.error(f"Error: {e}")
    st.stop()

# --- CHAT INTERFACE (Only shows after login) ---
st.title("🤖 Chatbot Live")
if prompt := st.chat_input("Ask me something..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        res = model.generate_content(prompt)
        st.markdown(res.text)
