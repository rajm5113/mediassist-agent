"""
tools/medication_reminder.py — Standard CRUD (Create, Read, Update, Delete)

🎓 WHAT THIS DOES:
   Similar to the symptom logger, it reads and writes to the SAME 
   `data/memory_store.json` file. It keeps "reminders" in their own list.
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

import config

# We use the same helper functions to load/save the JSON file
def _load_memory() -> dict:
    if not os.path.exists(config.MEMORY_FILE):
        return {}
    with open(config.MEMORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def _save_memory(data: dict):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def set_medication_reminder(medication: str, time: str, frequency: str, notes: Optional[str] = None) -> Dict[str, Any]:
    """Called by Gemini to create a new reminder."""
    store = _load_memory()
    reminders_list = store.get("reminders", [])

    new_reminder = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "medication": medication,
        "time": time,
        "frequency": frequency,
        "notes": notes,
        "active": True  # We can turn this to False if the user deletes it
    }

    reminders_list.append(new_reminder)
    store["reminders"] = reminders_list
    _save_memory(store)

    return {"status": "success", "message": f"Reminder set for {medication} at {time}."}


def list_reminders() -> Dict[str, Any]:
    """Called by Gemini when the user asks 'what are my reminders?'"""
    store = _load_memory()
    
    # We only want to return reminders that are still 'active'
    active_reminders = [r for r in store.get("reminders", []) if r.get("active") == True]
    
    return {
        "status": "success",
        "total_active": len(active_reminders),
        "reminders": active_reminders
    }

def get_all_active_reminders() -> list:
    """Helper function to fetch active reminders (used later by the summary tool)."""
    return list_reminders().get("reminders", [])
