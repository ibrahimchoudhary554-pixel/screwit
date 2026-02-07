import streamlit as st
import google.generativeai as genai
from streamlit_gsheets import GSheetsConnection
import os

st.set_page_config(page_title="The Bot That Finally Works", layout="centered")

# Initialize Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CONFIGURE GEMINI ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Updated model names - try the most common variants
    # Note: Using 'gemini-1.5-flash-latest' is more reliable
    model_names = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-pro', 'models/gemini-pro']
    model = None
    
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            # Test with a simple prompt to verify the model works
            test_response = model.generate_content("test")
            if test_response and hasattr(test_response, 'text'):
                st.success(f"✓ Using model: {name}")
                break
            else:
                model = None
        except Exception as e:
            continue
    
    if not model:
        st.error("Could not initialize any Gemini model. Please check your API key and model availability.")
        st.stop()
else:
    st.error("Add GEMINI_API_KEY to your Secrets!")
    st.stop()

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
            # Generate response with error handling
            with st.spinner("Thinking..."):
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=500,
                    )
                )
                
                if response.text:
                    st.markdown(response.text)
                    st.session_state.history.append({"role": "assistant", "content": response.text})
                else:
                    st.error("No response from AI. Please try again.")
                    
        except Exception as e:
            st.error(f"AI Error: {e}")
            st.info("Check if your API Key is active at [aistudio.google.com](https://aistudio.google.com)")
            
            # Optionally clear model and retry
            if "model" in st.session_state:
                del st.session_state.model

# Add a clear chat button in sidebar
with st.sidebar:
    st.header("Chat Controls")
    if st.button("Clear Chat History"):
        st.session_state.history = []
        st.rerun()
    st.divider()
    st.caption("Using Gemini API")
