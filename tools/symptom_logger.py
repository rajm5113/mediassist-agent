"""
tools/symptom_logger.py — Saves tracked symptoms to a local JSON file.

🎓 HOW IT WORKS:
   1. It checks if `data/memory_store.json` exists.
   2. It reads the current data (or creates empty data if new).
   3. It adds the new symptom (with a timestamp).
   4. It saves the file back to disk.
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

import config

def _ensure_data_dir():
    """Make sure the 'data/' folder exists before we try to save to it."""
    os.makedirs(config.DATA_DIR, exist_ok=True)

def _load_memory() -> dict:
    """Read the JSON file into a Python dictionary."""
    if not os.path.exists(config.MEMORY_FILE):
        return {}  # Return empty if file doesn't exist yet
    
    with open(config.MEMORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def _save_memory(data: dict):
    """Save the Python dictionary back to the JSON file."""
    _ensure_data_dir()
    with open(config.MEMORY_FILE, "w", encoding="utf-8") as file:
        # indent=2 makes the JSON file readable for humans!
        json.dump(data, file, indent=2, ensure_ascii=False)


def log_symptom(symptom: str, severity: Optional[int] = None, notes: Optional[str] = None) -> Dict[str, Any]:
    """
    Called by Gemini to record a new symptom.
    Returns a success message back to Gemini.
    """
    # 1. Grab everything currently saved
    store = _load_memory()
    
    # 2. Get the list of symptoms (or create an empty list if none exist)
    symptoms_list = store.get("symptoms", [])

    # 3. Create a new symptom record
    new_entry = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),  # Unique ID based on time
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symptom": symptom,
        "severity": severity,
        "notes": notes,
    }

    # 4. Add to list and save
    symptoms_list.append(new_entry)
    store["symptoms"] = symptoms_list
    _save_memory(store)

    # 5. Tell Gemini it worked
    return {
        "status": "success",
        "message": f"Logged '{symptom}' successfully.",
        "total_symptoms_tracked": len(symptoms_list)
    }

def get_all_symptoms() -> list:
    """Helper function to fetch all symptoms (used later by the summary tool)."""
    store = _load_memory()
    return store.get("symptoms", [])
