"""
config.py — Central settings for MediAssist AI Agent

🎓 WHAT THIS FILE DOES:
    Every file in this project imports from here instead of having
    settings scattered everywhere. Change one value here → it
    updates across the whole project.

🎓 WHAT python-dotenv DOES:
    `load_dotenv()` reads the `.env` file and loads the key=value
    pairs into the environment, so `os.getenv("GEMINI_API_KEY")`
    can find it — without us hardcoding the key in the code.
"""

import os
from dotenv import load_dotenv

# ── Load secrets from .env file ──────────────────────────────────────────────
load_dotenv()  # This reads .env and makes variables available via os.getenv()

# ── API Keys ─────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── Model Settings ───────────────────────────────────────────────────────────
MODEL_NAME        = "gemini-2.5-flash"   # Which Gemini model to use
TEMPERATURE       = 0.7                  # 0 = precise, 1 = creative
MAX_OUTPUT_TOKENS = 2048                 # Max length of response

# ── File Paths ───────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))  # Project root folder
DATA_DIR    = os.path.join(BASE_DIR, "data")              # Where saved data goes
MEMORY_FILE = os.path.join(DATA_DIR, "memory_store.json") # Single storage file

# ── OpenFDA Settings ─────────────────────────────────────────────────────────
OPENFDA_BASE_URL = "https://api.fda.gov/drug"

# ── App Info ─────────────────────────────────────────────────────────────────
APP_TITLE   = "MediAssist AI Agent"
APP_ICON    = "🏥"

