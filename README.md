# 🏥 MediAssist AI Agent

An autonomous healthcare productivity assistant built from scratch to demonstrate Agentic AI capabilities.

## 🚀 Features
This AI agent is powered by Google's Gemini 2.5 Flash and can perform the following autonomous tool-calls:
1. **OpenFDA Drug Lookup:** Fetches real, official drug side effects and dosages dynamically from `api.fda.gov`.
2. **Symptom Tracker:** Logs a user's health symptoms and severity scores locally.
3. **Medication Reminders:** Sets and records daily medication schedules.
4. **Health Summary:** Aggregates your logbook into a cleanly formatted markdown summary.

## 🧠 Architecture
- **Language Model:** Gemini 2.5 Flash / Gemini 2.0 Flash
- **Orchestration:** Custom logic using the official `google-generativeai` Python SDK (No heavy frameworks like LangChain).
- **Persistent Memory:** Sessions, symptoms, and reminders are saved to a local `data/memory_store.json` state so the agent never forgets past chats.
- **Frontend:** Built completely in pure Python using Streamlit (`ui/app.py`).

## 🛠️ Installation & Usage
1. Clone the repository: `git clone https://github.com/rajm5113/mediassist-agent.git`
2. Change into directory: `cd mediassist-agent`
3. Create a python virtual environment: `python -m venv .venv`
4. Install requirements: `pip install -r requirements.txt`
5. Create a `.env` file and add your Gemini API key: `GEMINI_API_KEY="AIzaSy...your-key-here"`
6. Run the agent: `streamlit run ui/app.py`

## 🎓 Learning Outcomes
This project was built step-by-step from an empty directory to learn:
- System Prompt Engineering
- JSON API Function Calling Protocols
- Python Environment Isolation (`.venv`)
- Short-term vs. Long-term LLM Session Memory
- Securing Secrets in Development
