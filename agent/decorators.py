"""
agent/decorators.py — Advanced Python Error Handling

🎓 WHAT IS A DECORATOR?
   A decorator wraps around another function to modify its behavior without changing the core function code.
   We use `@with_api_failover` to "wrap" the main chat function. If the chat function crashes, the decorator catches it and instantly redirects traffic to a backup API!
"""

import functools
import openai
from google.api_core import exceptions as google_exceptions

def with_api_failover(func):
    """
    Decorator that implements a 3-tier provider failover:
    1. Gemini
    2. Fallback to Groq
    3. Fallback to OpenRouter (Emergency)
    """
    @functools.wraps(func)
    def wrapper(self, user_message: str, uploaded_file=None, *args, **kwargs):
        try:
            # 1. PRIMARY ROUTE: Try the main Gemini function
            return func(self, user_message, uploaded_file, *args, **kwargs)
            
        except google_exceptions.ResourceExhausted:
            # 2. SECONDARY ROUTE: Gemini failed. Hit Groq.
            print("  ⚠️ [Cascade] Gemini Quota hit. Trying Groq...")
            from agent.llm_client import run_groq_fallback, run_openrouter_fallback
            
            try:
                fallback_answer = run_groq_fallback(self.session_memory.get_history(), user_message)
                self.session_memory.add_message("model", fallback_answer)
                self.persistent_memory.save_session(self.session_memory.get_history())
                return fallback_answer
                
            except openai.APIStatusError as groq_err:
                # 3. TERTIARY ROUTE: Groq failed (like Error 413 or 429). Hit OpenRouter.
                if groq_err.status_code in [413, 429]:
                    print("  ⚠️ [Cascade] Groq Rate Limit hit. Failing over to OpenRouter...")
                    try:
                        or_answer = run_openrouter_fallback(self.session_memory.get_history(), user_message)
                        self.session_memory.add_message("model", or_answer)
                        self.persistent_memory.save_session(self.session_memory.get_history())
                        return or_answer
                    except Exception as or_err:
                        err_msg = f"⚠️ **Total Failover:** All AI providers hit their limits. Final error: `{str(or_err)}`"
                        self.session_memory.add_message("model", err_msg)
                        return err_msg
                else:
                    err_msg = f"⚠️ **Groq API Error:** `{str(groq_err)}`"
                    self.session_memory.add_message("model", err_msg)
                    return err_msg
                    
        except Exception as e:
            # Catch all other random code crashes
            err_msg = f"⚠️ **System Error:** `{str(e)}`"
            self.session_memory.add_message("model", err_msg)
            return err_msg
            
    return wrapper
