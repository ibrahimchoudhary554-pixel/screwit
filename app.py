import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import os

# --- AUTH & CONFIG ---
st.set_page_config(page_title="Data-Fed Bot", layout="centered")

# Initialize Google Sheets for the "bouncer" (Login)
conn = st.connection("gsheets", type=GSheetsConnection)

# Configure Gemini
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- DATA LOADING ---
def load_training_data(filepath="data.txt"):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return "No training data found. The AI is currently as empty-headed as a Kardashian."

# Load that sweet, sweet data
knowledge_base = load_training_data()

# --- LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Security Check")
    user = st.text_input("username")
    pw = st.text_input("Password", type="password")
    
    if st.button("Enter the Matrix"):
        df = conn.read(worksheet="users")
        if ((df['username'] == user) & (df['password'] == pw)).any():
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Access Denied. Go sit in the corner.")
    st.stop()

# --- CHAT INTERFACE ---
st.title("🤖 The 'I Know Your Data' Bot")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Show the messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask me about your file..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Combine the file content with the user's question
    # We tell the AI: "Here is the Bible of Truth (data.txt), now answer the human."
    context_prompt = (
        f"You are a helpful assistant. Use the following context to answer the user's question.\n\n"
        f"CONTEXT FROM DATA.TXT:\n{knowledge_base}\n\n"
        f"USER QUESTION: {prompt}"
    )
    
    with st.chat_message("assistant"):
        try:
            response = model.generate_content(context_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Gemini had a stroke: {e}")
