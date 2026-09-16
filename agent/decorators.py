"""
agent/decorators.py — Provider failover for MediAssist.

A provider failure (including an unavailable model, invalid key, quota limit, or
temporary service error) moves to the next configured provider.
"""

import functools


def _save_fallback_answer(agent, user_message: str, answer: str) -> str:
    """Persist a fallback reply without duplicating the active user message."""
    history = agent.session_memory.get_history()
    if not history or history[-1].get("role") != "user" or history[-1].get("content") != user_message:
        agent.session_memory.add_message("user", user_message)
    agent.session_memory.add_message("model", answer)
    agent.persistent_memory.save_session(agent.session_memory.get_history())
    return answer


def with_api_failover(func):
    """Try Gemini, then Groq, then OpenRouter for any provider-level failure."""

    @functools.wraps(func)
    def wrapper(self, user_message: str, uploaded_file=None, *args, **kwargs):
        try:
            return func(self, user_message, uploaded_file, *args, **kwargs)
        except Exception as gemini_error:
            print(f"  ⚠️ [Cascade] Gemini failed: {gemini_error}. Trying Groq...")
            from agent.llm_client import run_groq_fallback, run_openrouter_fallback

            try:
                groq_answer = run_groq_fallback(
                    self.session_memory.get_history(),
                    user_message,
                )
                return _save_fallback_answer(self, user_message, groq_answer)
            except Exception as groq_error:
                print(f"  ⚠️ [Cascade] Groq failed: {groq_error}. Trying OpenRouter...")

                try:
                    openrouter_answer = run_openrouter_fallback(
                        self.session_memory.get_history(),
                        user_message,
                    )
                    return _save_fallback_answer(self, user_message, openrouter_answer)
                except Exception as openrouter_error:
                    error_message = (
                        "⚠️ **AI service unavailable:** All configured providers failed. "
                        "Please try again shortly."
                    )
                    print(
                        "  ⚠️ [Cascade] All providers failed — "
                        f"Gemini: {gemini_error}; Groq: {groq_error}; "
                        f"OpenRouter: {openrouter_error}"
                    )
                    return _save_fallback_answer(self, user_message, error_message)

    return wrapper
