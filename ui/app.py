"""
ui/app.py — The Streamlit Web Interface

🎓 WHAT IS THIS?
   Streamlit draws web pages using pure Python.
   - `st.title()` draws an H1 header.
   - `st.chat_message("user")` draws a chat bubble.
   - `st.chat_input()` draws the text box at the bottom.
   
   This file imports our Agent Core and connects it directly to the 
   buttons and text inputs of the website.
"""

import sys
import os
import streamlit as st

# Streamlit runs from the root folder, so we need to make sure 
# Python knows where to find our 'agent' and 'config' files.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
import pandas as pd
from agent.core import MediAssistAgent
from tools.symptom_logger import get_all_symptoms

# ─── 1. PAGE SETUP ───
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="centered"
)

# ─── 2. STATE MANAGEMENT ───
# Streamlit reruns this entire file from top to bottom every time you click a button.
# To stop it from creating a new AI Agent every time it reruns, we save the agent 
# into `st.session_state` (Streamlit's built-in memory).
@st.cache_resource
def get_agent():
    """Returns the same agent instance so we don't lose memory on button clicks."""
    return MediAssistAgent()

agent = get_agent()

# ─── 3. SIDEBAR (Tools & Settings) ───
with st.sidebar:
    st.header(f"{config.APP_ICON} {config.APP_TITLE}")
    st.write("Your personal healthcare productivity assistant.")
    st.write("---")
    
    # Reset Button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        agent.reset_session()
        st.success("History cleared!")
        
    st.write("---")
    
    # ─── SYMPTOM DASHBOARD ───
    st.subheader("📈 Symptom History")
    symptoms = get_all_symptoms()
    
    chart_data = []
    for s in symptoms:
        if s.get("severity") is not None:
            chart_data.append({
                "Date": s["timestamp"],
                "Symptom": s["symptom"].capitalize(),
                "Severity": int(s["severity"])
            })

    if chart_data:
        df = pd.DataFrame(chart_data)
        df["Date"] = pd.to_datetime(df["Date"])
        
        # Create a pivot table so each symptom gets its own colored line
        # aggregate by 'mean' so if 2 exist on the same second, it averages them
        pivot_df = pd.pivot_table(df, index="Date", columns="Symptom", values="Severity", aggfunc="mean")
        
        # Fill missing values forward so the line chart connects the dots smoothly
        pivot_df = pivot_df.ffill().fillna(0)
        
        st.line_chart(pivot_df, height=250)
    else:
        st.info("Tell me something like 'I have a headache, severity 6' to start your tracking chart!")

    st.write("---")
    st.caption("Built with Gemini 2.5 Flash & Streamlit")

# ─── 4. MAIN CHAT INTERFACE ───
st.title("Hi, I'm MediAssist! 👋")
st.write("I can look up FDA drug info, log your symptoms, and set reminders.")

# Draw the existing chat history
# We read this from our agent.session_memory so it matches exactly what Gemini sees.
for msg in agent.session_memory.get_history():
    # If the role is 'model', Streamlit prefers to call the icon 'assistant'
    role = "assistant" if msg["role"] == "model" else "user"
    with st.chat_message(role):
        st.markdown(msg["content"])

# ─── 5. USER INPUT BLOCK ───
# Allow uploading medical reports
uploaded_file = st.sidebar.file_uploader("📄 Upload Medical Report (PDF/Image)", type=["pdf", "png", "jpg", "jpeg"])

# st.chat_input waits for the user to type something and hit Enter
user_text = st.chat_input("Ask about a medication, log a symptom, or discuss the uploaded file...")

# If the user typed something:
if user_text:
    # A. Draw the user's message on the screen immediately
    with st.chat_message("user"):
        st.markdown(user_text)
        if uploaded_file:
            st.caption(f"📎 Attached: {uploaded_file.name}")

    # B. Show a spinning loading icon while the Brain thinks
    with st.chat_message("assistant"):
        with st.spinner("Thinking (and maybe reading your file/running tools)..."):
            # C. Send the text and the file to our Agent Core!
            reply = agent.chat(user_text, uploaded_file=uploaded_file)
            
        # D. The Brain is done. Draw the final answer on the screen.
        st.markdown(reply)
