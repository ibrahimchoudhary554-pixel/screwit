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
    
    # Try gemini-pro first (this is the free tier model)
    try:
        model = genai.GenerativeModel('gemini-pro')
        # Quick test to verify the model works
        test_response = model.generate_content("Hi")
        if test_response and hasattr(test_response, 'text'):
            st.success("✓ Using model: gemini-pro")
        else:
            st.error("Model test failed. Response invalid.")
            st.stop()
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")
        st.info("""
        Common issues:
        1. Make sure your API key is valid at https://aistudio.google.com
        2. Ensure you've enabled the Gemini API in Google Cloud
        3. Try using 'gemini-1.0-pro' if 'gemini-pro' doesn't work
        """)
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

# Display chat history
for m in st.session_state.history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Say something..."):
    # Add user message to history
    st.session_state.history.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        top_p=0.8,
                        top_k=40,
                        max_output_tokens=1024,
                    )
                )
                
                if response and response.text:
                    response_text = response.text
                    st.markdown(response_text)
                    # Add assistant response to history
                    st.session_state.history.append({"role": "assistant", "content": response_text})
                else:
                    error_msg = "No response from AI. Please try again."
                    st.error(error_msg)
                    
        except Exception as e:
            error_msg = f"AI Error: {str(e)}"
            st.error(error_msg)
            st.info("Check if your API Key is active at [aistudio.google.com](https://aistudio.google.com)")

# Sidebar controls
with st.sidebar:
    st.header("Chat Controls")
    if st.button("Clear Chat History"):
        st.session_state.history = []
        st.rerun()
    
    st.divider()
    st.subheader("Debug Info")
    st.write(f"Messages in history: {len(st.session_state.history)}")
    
    if st.button("Test Model Connection"):
        try:
            test_response = model.generate_content("Say 'Connection successful' if you can hear me.")
            st.success(f"✓ Connection test passed: {test_response.text[:50]}...")
        except Exception as e:
            st.error(f"✗ Test failed: {e}")
