"""
agent/core.py — The Orchestrator (The Main Brain)

🎓 WHAT IS THIS?
   This is the final puzzle piece before the UI. It glues everything together:
     1. It loads our API key and configures the Gemini SDK.
     2. It attaches our Memory so Gemini remembers things.
     3. It sends your message to Gemini.
     4. If Gemini wants a tool, it asks the Router to run it, then sends 
        the result back to Gemini to get the final answer.
     5. It returns that final text answer back to you (or the Streamlit UI).
"""

import google.generativeai as genai

import config
from agent.identity import SYSTEM_PROMPT, TOOL_DECLARATIONS
from agent.router import route_tool_call
from memory.session_memory import SessionMemory
from memory.persistent_memory import PersistentMemory

def _format_tools_for_gemini():
    """
    Helper function: Converts our simple Python tool list (in identity.py)
    into the strict "protobuf" format that Google's SDK requires.
    """
    declarations = []
    for t in TOOL_DECLARATIONS:
        # Build the properties dict
        props = {}
        for param_name, param_details in t["parameters"].get("properties", {}).items():
            param_type_str = param_details["type"].upper()
            props[param_name] = genai.protos.Schema(
                type=getattr(genai.protos.Type, param_type_str),
                description=param_details.get("description", "")
            )
            
        # Build the final schema
        schema = genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties=props,
            required=t["parameters"].get("required", [])
        )
        
        dec = genai.protos.FunctionDeclaration(
            name=t["name"],
            description=t["description"],
            parameters=schema
        )
        declarations.append(dec)
        
    return [genai.protos.Tool(function_declarations=declarations)]


class MediAssistAgent:
    def __init__(self):
        # 1. Boot up the Google AI API using our secret key
        genai.configure(api_key=config.GEMINI_API_KEY)

        # 2. Create the Gemini AI Model instance
        self.model = genai.GenerativeModel(
            model_name=config.MODEL_NAME,
            system_instruction=SYSTEM_PROMPT,
            tools=_format_tools_for_gemini(),
            generation_config=genai.types.GenerationConfig(
                temperature=config.TEMPERATURE,
                max_output_tokens=config.MAX_OUTPUT_TOKENS,
            )
        )

        # 3. Attach our memory modules
        self.session_memory = SessionMemory()
        self.persistent_memory = PersistentMemory()

        # 4. Try to load the last conversation if we crashed or restarted
        last_history = self.persistent_memory.load_last_session()
        
        # Convert our {"role": ..., "content": ...} dicts into Gemini format
        gemini_history = []
        for msg in last_history:
            gemini_history.append({
                "role": msg["role"],
                "parts": [msg["content"]]
            })
        
        # 5. Start the chat session
        self._chat = self.model.start_chat(history=gemini_history)

    def chat(self, user_message: str) -> str:
        """
        Send a message, handle any tool calls loop, and get the final text response.
        """
        from google.api_core import exceptions as google_exceptions
        
        # Save user message to short-term memory
        self.session_memory.add_message("user", user_message)

        try:
            # Send it to Gemini
            response = self._chat.send_message(user_message)

            # ─── MIGHT NEED A TOOL LOOP ───
            # Gemini 2.x also supports "Parallel Function Calling" (doing 2 tools at once!)
            while True:
                # 1. Gather all function calls Gemini wants us to run right now
                tool_responses = []
                
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "function_call") and getattr(part.function_call, "name", ""):
                        fn_call = part.function_call
                        fn_name = fn_call.name
                        fn_args = dict(fn_call.args)
                        
                        print(f"  [Agent is using tool: {fn_name} ...]")
                        
                        # Run the tool!
                        tool_result_json_str = route_tool_call(fn_name, fn_args)
                        
                        # Package the result for Gemini
                        tool_responses.append(
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=fn_name,
                                    response={"result": tool_result_json_str}
                                )
                            )
                        )

                # 2. Did we find any tools to run?
                if tool_responses:
                    # Send ALL the tool results back to Gemini at the exact same time
                    response = self._chat.send_message(
                        genai.protos.Content(
                            role="tool",
                            parts=tool_responses
                        )
                    )
                else:
                    # No more tools. Gemini just gave us a text string. The loop is done!
                    break

            # Safely extract text (bypasses SDK ValueError if model hallucinates an empty function_call part alongside the text)
            text_parts = []
            for p in response.candidates[0].content.parts:
                # Check if this part contains valid text
                if hasattr(p, "text") and getattr(p, "text", ""):
                    text_parts.append(p.text)
                    
            final_answer = " ".join(text_parts) if text_parts else "Done."

            # Save the final text and flush short-term memory to long-term memory file
            self.session_memory.add_message("model", final_answer)
            self.persistent_memory.save_session(self.session_memory.get_history())

            return final_answer
            
        except google_exceptions.ResourceExhausted:
            error_msg = "⚠️ **Oops!** I'm currently experiencing high traffic and have hit my free-tier limit. Please wait a minute and try again!"
            self.session_memory.add_message("model", error_msg)
            return error_msg
            
        except Exception as e:
            error_msg = f"⚠️ **System Error:** I encountered an unexpected issue while thinking.\n\n`{str(e)}`"
            self.session_memory.add_message("model", error_msg)
            return error_msg

    def reset_session(self):
        """Wipes the short term memory to start a fresh conversation."""
        self.session_memory.clear()
        self._chat = self.model.start_chat(history=[])
