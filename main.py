"""
main.py — The CLI Tester

🎓 WHAT IS THIS?
   Before we build the fancy web app, we want to test that our 
   Agent Core actually works. This script lets us chat with 
   MediAssist directly in the terminal to verify the "Brain" is working.
"""

from agent.core import MediAssistAgent

def run_test():
    print("🤖 Booting up MediAssist Brain...\n")
    agent = MediAssistAgent()
    
    # Let's ask a question that forces Gemini to use the drug_lookup tool
    test_message = "What are the common side effects of amoxicillin?"
    
    print(f"🧑 You: {test_message}")
    print("🏥 MediAssist: Thinking (and maybe using tools)...\n")
    
    # Send the message!
    reply = agent.chat(test_message)
    
    print("--- Final Answer ---")
    print(reply)
    print("--------------------")

if __name__ == "__main__":
    run_test()
