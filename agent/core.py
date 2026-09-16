"""
agent/core.py — The Gemini orchestrator for MediAssist.

Uses the maintained Google GenAI SDK and manually executes the app's local
health tools when Gemini requests them.
"""

from google import genai
from google.genai import types

import config
from agent.decorators import with_api_failover
from agent.identity import SYSTEM_PROMPT, TOOL_DECLARATIONS
from agent.router import route_tool_call
from memory.persistent_memory import PersistentMemory
from memory.session_memory import SessionMemory
from tools.web_search import SEARCH_TRIGGER_KEYWORDS


def _tool_config():
    """Return the custom function declarations in the current Gemini SDK format."""
    return [types.Tool(function_declarations=TOOL_DECLARATIONS)]


def _history_contents(history):
    """Convert saved chat memory into Gemini content objects."""
    contents = []
    for message in history:
        role = "model" if message.get("role") == "model" else "user"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=message.get("content", ""))],
            )
        )
    return contents


def _uploaded_file_part(uploaded_file):
    """Create an inline Gemini part for an uploaded PDF or image."""
    mime_type = getattr(uploaded_file, "type", None)
    if not mime_type:
        name = uploaded_file.name.lower()
        mime_type = "application/pdf" if name.endswith(".pdf") else "image/jpeg"

    return types.Part.from_bytes(
        data=uploaded_file.getvalue(),
        mime_type=mime_type,
    )


def _response_text(response):
    """Safely extract text without assuming every response part is text."""
    text_parts = []
    for candidate in response.candidates or []:
        for part in candidate.content.parts or []:
            text = getattr(part, "text", None)
            if text:
                text_parts.append(text)
    return " ".join(text_parts).strip()


class MediAssistAgent:
    def __init__(self):
        # Keep the UI usable when Gemini is not configured; the failover
        # decorator can still serve Groq or OpenRouter responses.
        self.client = genai.Client(api_key=config.GEMINI_API_KEY) if config.GEMINI_API_KEY else None
        self.session_memory = SessionMemory()
        self.persistent_memory = PersistentMemory()

    def _generate(self, contents):
        if not self.client:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        return self.client.models.generate_content(
            model=config.MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=_tool_config(),
                temperature=config.TEMPERATURE,
                max_output_tokens=config.MAX_OUTPUT_TOKENS,
                automatic_function_calling={"disable": True},
            ),
        )

    @with_api_failover
    def chat(self, user_message: str, uploaded_file=None) -> str:
        """Send a prompt, run any requested local tools, then return Gemini's reply."""
        message_text = user_message
        if uploaded_file:
            message_text += (
                "\n\n[The user attached a medical report. Analyze the attached file "
                "when it is relevant to the request.]"
            )

        needs_search = any(keyword in user_message.lower() for keyword in SEARCH_TRIGGER_KEYWORDS)
        search_hint = (
            "\n\n[SYSTEM HINT: Web search is available if you need up-to-date information.]"
            if needs_search
            else "\n\n[SYSTEM HINT: Answer from existing knowledge. Do NOT call web_search.]"
        )

        current_parts = [types.Part.from_text(text=message_text + search_hint)]
        if uploaded_file:
            current_parts.append(_uploaded_file_part(uploaded_file))

        contents = _history_contents(self.session_memory.get_history())
        contents.append(types.Content(role="user", parts=current_parts))

        max_turns = 5
        for _ in range(max_turns):
            response = self._generate(contents)
            candidate = (response.candidates or [None])[0]
            if not candidate or not candidate.content:
                raise RuntimeError("Gemini returned no usable response.")

            function_calls = [
                part.function_call
                for part in candidate.content.parts or []
                if getattr(part, "function_call", None)
                and getattr(part.function_call, "name", None)
            ]

            if not function_calls:
                final_answer = _response_text(response) or "Done."
                memory_text = user_message + (
                    f"\n[User attached file: {uploaded_file.name}]" if uploaded_file else ""
                )
                self.session_memory.add_message("user", memory_text)
                self.session_memory.add_message("model", final_answer)
                self.persistent_memory.save_session(self.session_memory.get_history())
                return final_answer

            # Preserve Gemini's returned content (including tool-call context) before
            # appending the tool results for the next model turn.
            contents.append(candidate.content)
            tool_results = []
            for function_call in function_calls:
                function_name = function_call.name
                function_args = dict(function_call.args or {})
                print(f"  [Gemini] using tool: {function_name} ...")
                result_json = route_tool_call(function_name, function_args)
                tool_results.append(
                    types.Part.from_function_response(
                        name=function_name,
                        response={"result": result_json},
                    )
                )

            contents.append(types.Content(role="user", parts=tool_results))

        raise RuntimeError("Gemini reached the maximum number of tool-call turns.")

    def reset_session(self):
        """Wipe short-term memory to start a new conversation."""
        self.session_memory.clear()
