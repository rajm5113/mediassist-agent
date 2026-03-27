"""
memory/persistent_memory.py — Long-term memory (Hard Drive)

🎓 WHAT IS THIS?
   While the tools save *data* (like remiders) to the JSON file, 
   we also want to save the *chat history* so if the app crashes, 
   we can resume the conversation.
   
   This class writes the final `SessionMemory` into the same 
   JSON file that the tools use.
"""

import json
import os
from datetime import datetime
from typing import List, Dict

import config

class PersistentMemory:
    def __init__(self):
        os.makedirs(config.DATA_DIR, exist_ok=True)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Creates the JSON file with an empty skeleton if it's missing."""
        if not os.path.exists(config.MEMORY_FILE):
            empty_data = {
                "sessions": [],
                "symptoms": [],
                "reminders": []
            }
            with open(config.MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(empty_data, f, indent=2)

    def _read(self) -> dict:
        with open(config.MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict):
        with open(config.MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_session(self, history: List[Dict[str, str]]):
        """Takes the conversation history and saves it to the JSON file."""
        if not history:
            return  # Don't save empty sessions
            
        store = self._read()
        sessions = store.get("sessions", [])

        # Create a snapshot of this session
        session_snapshot = {
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "turns": len(history),
            "history": history
        }

        # We append it to the master list. 
        # (We keep the last 50 sessions so the file doesn't grow to 5 gigabytes)
        sessions.append(session_snapshot)
        if len(sessions) > 50:
            sessions = sessions[-50:]

        store["sessions"] = sessions
        self._write(store)

    def load_last_session(self) -> List[Dict[str, str]]:
        """Used when the app boots up: loads the very last conversation."""
        store = self._read()
        sessions = store.get("sessions", [])
        if sessions:
            return sessions[-1].get("history", [])
        return []
