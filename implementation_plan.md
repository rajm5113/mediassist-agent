# MediAssist AI Agent — What We're Building

## What Is This Project?

A **healthcare productivity AI agent** that can:
- 🔍 Look up real drug information (from the official US FDA database)
- 📋 Log and track symptoms with severity scores
- 💊 Set and manage medication reminders
- 📄 Generate a health summary report

Built with **Google Gemini 2.0 Flash** (free API) as the brain, and a clean **Streamlit** web interface.

---

## How the Pieces Fit Together

```
Your Message
     │
     ▼
[ Streamlit UI ]  ← What the user sees (web browser)
     │
     ▼
[ Agent Core ]    ← Sends your message to Gemini
     │
     ├──── Gemini says "call a tool" ──► [ Router ] ──► [ Tool ]
     │         (e.g. lookup_drug)                     (calls OpenFDA API)
     │
     └──── Gemini says "here's the answer" ──► shown to you
```

---

## The Learning Road Map

We go through **8 steps**, one at a time. You approve each step before I build it.

| Step | What we build | Key concept you'll learn |
|------|--------------|--------------------------|
| 1 | Folder + virtual env | Python project isolation |
| 2 | `.env` + `config.py` | Secret management |
| 3 | System prompt | How LLMs get their personality |
| 4 | Tools (drug, symptom, reminder, summary) | API calls + file I/O |
| 5 | Memory | Session vs persistent state |
| 6 | Agent core | Function-calling / agentic loop |
| 7 | Streamlit UI | Web app from Python |
| 8 | GitHub + deploy | Real-world shipping |

---

## Tech Stack

| What | Tool | Why |
|------|------|-----|
| LLM | Google Gemini 2.0 Flash | Free tier, supports function-calling |
| Drug data | OpenFDA API | Free, no key needed |
| Web UI | Streamlit | Python-native, zero HTML needed |
| Storage | JSON file | Simple, no database needed for learning |
| Secrets | `.env` + `python-dotenv` | Industry standard |

---

## Verification Plan

At each step we will:
1. **Read** the file we just wrote together
2. **Run** a small test in the terminal to confirm it works
3. Only move to next step once you're comfortable

No automated tests — we verify manually at each step since this is a learning project.

---

> **Teaching approach:** I explain every concept before writing code. You ask questions anytime. I do NOT proceed to the next step without your go-ahead.
