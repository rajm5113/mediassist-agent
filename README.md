# 🏥 MediAssist AI Agent

> **Your personal AI-powered healthcare productivity assistant** — built from scratch to demonstrate real-world Agentic AI capabilities.

MediAssist is a fully autonomous, multi-tool AI agent that can look up drug information, log symptoms, set medication reminders, check dangerous drug interactions, search the latest medical news, and even listen and talk back — all from a clean Streamlit web interface.

---

## 📸 What Does It Look Like?

When you open the app, you'll see a **dark-themed chat interface** where you can:
- Type a message (e.g. *"What are the side effects of ibuprofen?"*)
- Or speak into the microphone and hear the answer read back to you
- Watch the **live symptom chart** in the sidebar update in real time

---

## ✨ Features

### 🤖 AI & Intelligence
| Feature | Description |
|---|---|
| **Multi-model Support** | Switch between Gemini 2.5 Flash, Groq Llama 3.3 70B, Groq Llama 3.1 8B, or OpenRouter Llama 3 8B from the sidebar — **no restart needed** |
| **3-Tier Auto-Failover** | If Gemini's quota is hit, the agent automatically falls back to Groq, then OpenRouter — you'll never see a blank answer |
| **Autonomous Tool Calling** | The AI decides which tool to run (drug lookup, symptom log, web search, etc.) based on what you say — no buttons to click |
| **Proactive Symptom Logging** | Just say *"I have a headache, severity 6"* and it immediately saves it without you having to ask |

### 💊 Healthcare Tools
| Tool | What It Does |
|---|---|
| **FDA Drug Lookup** | Fetches real, official drug information (uses, warnings, side effects, dosage) from the live `api.fda.gov` database |
| **Symptom Tracker** | Logs symptoms with severity scores (1–10) and timestamps to a local JSON file |
| **Drug Interaction Checker** | Warns you about dangerous combinations (e.g. Ibuprofen + Lisinopril → kidney risk) |
| **Medication Reminders** | Sets and stores daily/weekly medication schedules |
| **Health Summary Report** | Generates a formatted markdown summary of all your logged symptoms and reminders |
| **Live Medical Web Search** | Searches DuckDuckGo and PubMed for the latest drug approvals, recalls, and clinical trials — **only triggered when necessary** |

### 🎤 Voice Mode
- **Speak instead of type** — powered by **Groq Whisper Large v3 Turbo** (state-of-the-art accuracy, especially for medical terms and non-native accents)
- **Replies read aloud** — toggle "Read replies aloud" and the agent speaks its response back via Google Text-to-Speech

### 📈 Live Symptom Dashboard
- A **real-time interactive line chart** in the sidebar shows all your logged symptoms over time
- Each symptom gets its own colored line (e.g. "Fever" vs. "Headache")
- Updates instantly after every symptom log — no page refresh needed

### 🧠 Memory System
- **Short-term memory** — the agent remembers the full conversation in the current session
- **Long-term memory** — past sessions, symptoms, and reminders are saved to `data/memory_store.json` so your health history is never lost

### 📄 File Analysis
- Upload **PDFs** or **images** (medical reports, prescriptions, lab results) and the agent can read and analyze them using Gemini's vision capabilities

---

## 🏗️ Architecture

```
mediassist-agent/
│
├── ui/
│   └── app.py              ← Streamlit web interface (the face of the app)
│
├── agent/
│   ├── core.py             ← Orchestrator: connects UI ↔ Gemini ↔ Tools
│   ├── identity.py         ← System prompt + tool declarations
│   ├── router.py           ← Tool dispatcher: routes LLM tool calls to Python functions
│   ├── llm_client.py       ← Multi-provider LLM router (Groq / OpenRouter fallbacks)
│   └── decorators.py       ← @with_api_failover: auto-retry on quota errors
│
├── tools/
│   ├── drug_lookup.py      ← Calls api.fda.gov
│   ├── symptom_logger.py   ← Saves/reads symptoms from memory_store.json
│   ├── medication_reminder.py ← Saves/reads reminders
│   ├── health_summary.py   ← Generates markdown health reports
│   ├── interaction_checker.py ← Drug-drug interaction database
│   ├── web_search.py       ← DuckDuckGo + PubMed smart search
│   └── voice.py            ← Groq Whisper STT + gTTS text-to-speech
│
├── memory/
│   ├── session_memory.py   ← In-session chat history
│   └── persistent_memory.py ← Read/write to data/memory_store.json
│
├── data/
│   └── memory_store.json   ← Your personal health data (auto-created)
│
├── config.py               ← Central configuration (loads .env keys)
├── requirements.txt        ← All Python dependencies
└── .env                    ← Your secret API keys (never commit this!)
```

**How a message flows through the system:**
```
You type "I have a fever, severity 7"
         │
         ▼
[Layer 1 Filter] → No search keywords → web_search BLOCKED
         │
         ▼
[Gemini 2.5 Flash] → Decides: "I should call log_symptom"
         │
         ▼
[router.py] → Runs tools/symptom_logger.py → Saves to memory_store.json
         │
         ▼
[Gemini] → Writes final reply: "I've logged your fever (severity 7)..."
         │
         ▼
[Streamlit UI] → Shows reply + updates sidebar chart
```

---

## 🛠️ Installation & Setup

### Prerequisites
- **Python 3.10+** installed on your machine
- A **Gemini API key** (free at [aistudio.google.com](https://aistudio.google.com))
- Optionally: **Groq API key** (free at [console.groq.com](https://console.groq.com)) and **OpenRouter API key** (free at [openrouter.ai](https://openrouter.ai))

### Step-by-step

**1. Clone the repository**
```bash
git clone https://github.com/rajm5113/mediassist-agent.git
cd mediassist-agent
```

**2. Create a virtual environment**
```bash
python -m venv .venv
```

**3. Activate it**
```bash
# Windows
.venv\Scripts\activate

# Mac / Linux
source .venv/bin/activate
```

**4. Install all dependencies**
```bash
pip install -r requirements.txt
```

**5. Create your `.env` file**

Create a file named `.env` in the root folder and add your API keys:
```env
GEMINI_API_KEY="AIzaSy...your-key-here"

# Optional — enables Groq fallback + Whisper voice transcription
GROQ_API_KEY="gsk_...your-key-here"

# Optional — enables OpenRouter fallback
OPENROUTER_API_KEY="sk-or-v1-...your-key-here"
```

> **Note:** The `.env` file is in `.gitignore` — it will **never** be uploaded to GitHub. Keep your keys safe.

**6. Run the app**
```bash
.venv\Scripts\streamlit run ui\app.py
```

Then open **http://localhost:8501** in your browser.

---

## 🧪 Things to Try

Once the app is running, paste these into the chat to test each feature:

| What to say | What the agent does |
|---|---|
| `"What are the side effects of metformin?"` | Calls FDA API, returns official warnings |
| `"I have a headache, severity 5, since this morning"` | Logs symptom → chart updates in sidebar |
| `"Is it safe to take Ibuprofen and Lisinopril together?"` | Runs drug interaction check |
| `"Remind me to take Vitamin D every morning at 8am"` | Saves a medication reminder |
| `"Generate my health summary"` | Produces a formatted report of all your data |
| `"What are the latest clinical trials for metformin?"` | Triggers web search → PubMed results |
| `"Is there a recent FDA recall for any blood pressure drug?"` | Web search → DuckDuckGo results |

**To test Voice Mode:**
1. Toggle **"Enable Voice Mode"** in the sidebar
2. Click the mic and say *"I have a fever, severity 7"*
3. Enable **"Read replies aloud"** to hear the agent speak back

---

## 🔑 API Keys — Where to Get Them

| Key | Where | Cost |
|---|---|---|
| `GEMINI_API_KEY` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Free tier available |
| `GROQ_API_KEY` | [console.groq.com/keys](https://console.groq.com/keys) | Free tier (generous limits) |
| `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) | Free tier (Llama 3 8B is free) |

---

## ⚠️ Important Notes

- **This is not a substitute for medical advice.** MediAssist is an AI tool for productivity and information lookup only. Always consult a licensed healthcare provider for diagnosis or treatment.
- **Your data stays local.** All symptoms and reminders are saved to `data/memory_store.json` on your own machine — nothing is sent to any external server except the LLM APIs.
- **The Gemini package will show a `FutureWarning`** about the deprecated `google.generativeai` SDK. The app works perfectly despite this warning — migration to the new SDK is a planned improvement.

---

## 📚 How It Was Built (Step-by-Step)

This project was built from an **empty folder** in 15 progressive steps as a learning exercise in Agentic AI:

| Step | What Was Built |
|---|---|
| 1–3 | Project scaffold, config, `.env` loading |
| 4 | Gemini API integration + system prompt |
| 5 | Short-term session memory |
| 6 | FDA Drug Lookup tool (first tool call!) |
| 7 | Symptom logging tool |
| 8 | Medication reminder tool |
| 9 | Persistent memory (save/load JSON) |
| 10 | PDF & image file analysis (Gemini vision) |
| 11 | Multi-provider LLM fallback (Groq + OpenRouter) |
| 12 | Drug-Drug Interaction Checker |
| 13 | Live Symptom Dashboard (real-time chart) |
| 14 | Voice Mode (Whisper STT + gTTS TTS) |
| 15 | Live Medical Web Search (DuckDuckGo + PubMed) |

---

## 🧠 Key Technical Concepts Demonstrated

- **Agentic AI** — autonomous tool selection and multi-step reasoning
- **Function Calling / Tool Use** — Gemini decides which Python function to run
- **Multi-Provider LLM Routing** — seamless failover between 3 AI providers
- **Graceful Degradation** — errors caught and recovered without crashing the UI
- **System Prompt Engineering** — shaping AI behavior with explicit rules
- **Session + Persistent Memory** — short-term chat history + long-term JSON storage
- **Layer 1 Pre-filtering** — keyword-based gate to prevent unnecessary API calls
- **Whisper Voice Transcription** — production-grade STT with medical vocabulary priming

---

## 👨‍💻 Built By

**Raj Mishra** — [@rajm5113](https://github.com/rajm5113)

> *"Built step by step from scratch to learn every layer of how AI agents really work."*
