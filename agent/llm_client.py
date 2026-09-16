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
    """
    Translates our custom tool list into the OpenAI/Groq JSON Schema format.
    NOTE: web_search is EXCLUDED here because Groq/OpenRouter's Llama models
    produce malformed tool calls for it. web_search only works via Gemini's
    native function calling. The fallback providers handle the core 5 tools.
    """
    # Tools that Groq/OpenRouter Llama models reliably support
    SUPPORTED_IN_FALLBACK = {
        "lookup_drug", "log_symptom", "set_medication_reminder",
        "list_reminders", "generate_health_summary", "check_drug_interaction"
    }

    tools = []
    for t in TOOL_DECLARATIONS:
        if t["name"] not in SUPPORTED_IN_FALLBACK:
            continue   # ← skip web_search for fallback providers

        properties = {}
        for prop_name, prop_data in t["parameters"].get("properties", {}).items():
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


def _append_user_message(messages, session_history, user_message: str):
    """Avoid duplicating the active user message during automatic failover."""
    if not session_history or session_history[-1].get("role") != "user" or session_history[-1].get("content") != user_message:
        _append_user_message(messages, session_history, user_message)


def run_groq_fallback(session_history, user_message: str, model: str | None = None) -> str:
    """
    Connects to Groq using a current tool-capable model.
    The default can be overridden with the GROQ_MODEL environment variable.
    """
    import openai as openai_module
    if not config.GROQ_API_KEY:
        raise openai_module.APIStatusError(message="Groq API key not found", response=None, body=None)

    model = model or config.GROQ_MODEL
    client = OpenAI(api_key=config.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    print(f"  [Groq] Using model: {model}")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in session_history:
        role = "assistant" if msg["role"] == "model" else "user"
        messages.append({"role": role, "content": msg["content"]})
        
    _append_user_message(messages, session_history, user_message)

    max_turns = 5
    for _ in range(max_turns):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=_get_openai_tools(),
                temperature=config.TEMPERATURE
            )
        except Exception as e:
            # Groq returns 400 'tool_use_failed' when model generates bad tool syntax.
            # Retry once as plain chat (no tools) so the user still gets an answer.
            if "tool_use_failed" in str(e):
                print(f"  [Groq] tool_use_failed — retrying as plain chat...")
                plain_response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=config.TEMPERATURE
                )
                return plain_response.choices[0].message.content or "Done."
            raise  # re-raise unknown errors

        response_message = response.choices[0].message
        messages.append(response_message)

        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                print(f"  [Groq] using tool: {fn_name} ...")
                result_json = route_tool_call(fn_name, fn_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": result_json
                })
        else:
            return response_message.content or "Done."

    return "⚠️ **Groq Error:** Model reached max tool-call turns."


def run_openrouter_fallback(session_history, user_message: str, model: str | None = None, supports_tools: bool = False) -> str:
    """
    Connects to OpenRouter. Defaults to its free-model router so a retired free model does not break the fallback.
    supports_tools=False → plain chat mode (for free models that can't handle tool schemas).
    """
    if not config.OPENROUTER_API_KEY:
        raise Exception("OpenRouter API key not found in .env")

    model = model or config.OPENROUTER_MODEL
    client = OpenAI(api_key=config.OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
    print(f"  [OpenRouter] Using model: {model} | tools: {supports_tools}")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in session_history:
        role = "assistant" if msg["role"] == "model" else "user"
        messages.append({"role": role, "content": msg["content"]})
        
    _append_user_message(messages, session_history, user_message)

    # ── Plain chat mode (no tools) — for free/limited models ──
    if not supports_tools:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=config.TEMPERATURE
        )
        return response.choices[0].message.content or "Done."

    # ── Full tool-calling mode ──
    max_turns = 5
    for _ in range(max_turns):
        response = client.chat.completions.create(
            model=model,
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
                print(f"  [OpenRouter] using tool: {fn_name} ...")
                result_json = route_tool_call(fn_name, fn_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": result_json
                })
        else:
            return response_message.content or "Done."
            
    return "⚠️ **OpenRouter Error:** Model reached max tool-call turns."
