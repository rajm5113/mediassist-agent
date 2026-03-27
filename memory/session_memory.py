"""
memory/session_memory.py — Short-term memory (RAM)

🎓 WHAT IS THIS?
   When you chat with Gemini, it doesn't automatically remember what you 
   said 5 minutes ago. You have to send the ENTIRE conversation history 
   every single time you ask a new question.
   
   SessionMemory is a simple list that holds the current conversation.
   If you close the app, this gets wiped clean (just like RAM).
"""

from typing import List, Dict

class SessionMemory:
    def __init__(self):
        # This list holds the back-and-forth chat.
        # Format: [{"role": "user", "content": "Hi"}, {"role": "model", "content": "Hello"}]
        self._history: List[Dict[str, str]] = []
        
        # We only keep the last 20 messages. 
        # If we send 10,000 messages to Gemini, it costs too much money and 
        # hits the "context limit" (the AI gets confused).
        self.max_history = 20

    def add_message(self, role: str, content: str):
        """Add a new message to the history."""
        self._history.append({"role": role, "content": content})
        
        # If the list gets too long, drop the oldest messages
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]

    def get_history(self) -> List[Dict[str, str]]:
        """Return a copy of the history to send to Gemini."""
        return list(self._history)

    def clear(self):
        """Wipe the current session (called when user clicks 'New Chat')."""
        self._history = []
