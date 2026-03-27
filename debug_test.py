from agent.core import MediAssistAgent
import config

agent = MediAssistAgent()
print("Sending headache prompt...")
response = agent._chat.send_message("I have a headache, severity 4, started this morning")

print("\n--- RAW RESPONSE PARTS ---")
for i, part in enumerate(response.candidates[0].content.parts):
    print(f"Part {i}: {type(part)}")
    print(part)

print("\n--- FUNCTION CALLS PROPERTY ---")
print(response.function_calls)
