"""
agent/llm_client.py — The Multi-Provider Fallback Router

🎓 WHAT IS THIS?
   When the primary AI (Gemini) hits a rate limit and crashes, this router 
   automatically kicks in and forwards the exact same task to a backup AI (Groq or OpenRouter).
   
   Because Gemini and OpenAI use different formats for "Tools", this file 
   translates our Python tool dictionaries into the OpenAI standard so any 
   model can use them.
"""

import json
import config
from openai import OpenAI
from agent.identity import SYSTEM_PROMPT, TOOL_DECLARATIONS
from agent.router import route_tool_call

def _get_openai_tools():
    """Translates our custom tool list into the OpenAI/Groq JSON Schema format."""
    tools = []
    for t in TOOL_DECLARATIONS:
        # Build standard OpenAI tool format
        properties = {}
        for prop_name, prop_data in t["parameters"].get("properties", {}).items():
            # OpenAI requires types to be lowercase (e.g. "string" instead of "STRING")
            properties[prop_name] = {
                "type": prop_data["type"].lower(),
                "description": prop_data.get("description", "")
            }
            
        tools.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": t["parameters"].get("required", [])
                }
            }
        })
    return tools

def run_groq_fallback(session_history, user_message: str) -> str:
    """
    Kicks in when Gemini fails. Connects to Groq's insanely fast inference engine.
    """
    if not config.GROQ_API_KEY:
        raise openai.APIStatusError(message="Groq API key not found", response=None, body=None)

    client = OpenAI(api_key=config.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in session_history:
        role = "assistant" if msg["role"] == "model" else "user"
        messages.append({"role": role, "content": msg["content"]})
        
    messages.append({"role": "user", "content": user_message})

    max_turns = 5
    for _ in range(max_turns):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=_get_openai_tools(),
            temperature=config.TEMPERATURE
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                print(f"  [Groq Fallback] using tool: {fn_name} ...")
                
                result_json = route_tool_call(fn_name, fn_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": result_json
                })
        else:
            return response_message.content or "Done."
            
    return "⚠️ **Groq Error:** The model got stuck in an infinite loop and was forcefully stopped to save tokens."


def run_openrouter_fallback(session_history, user_message: str) -> str:
    """
    Kicks in when BOTH Gemini and Groq fail. Connects to OpenRouter.
    """
    if not config.OPENROUTER_API_KEY:
        raise Exception("OpenRouter API key not found in .env")

    client = OpenAI(api_key=config.OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in session_history:
        role = "assistant" if msg["role"] == "model" else "user"
        messages.append({"role": role, "content": msg["content"]})
        
    messages.append({"role": "user", "content": user_message})

    max_turns = 5
    for _ in range(max_turns):
        response = client.chat.completions.create(
            # Using a fast, reliable model on OpenRouter
            model="meta-llama/llama-3-8b-instruct:free",
            messages=messages,
            tools=_get_openai_tools(),
            temperature=config.TEMPERATURE
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                print(f"  [OpenRouter Fallback] using tool: {fn_name} ...")
                
                result_json = route_tool_call(fn_name, fn_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": result_json
                })
        else:
            return response_message.content or "Done."
            
    return "⚠️ **OpenRouter Error:** The model got stuck in an infinite loop."
