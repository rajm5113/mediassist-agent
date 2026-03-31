"""
agent/identity.py — Who is MediAssist? What can it do?

🎓 TWO THINGS LIVE HERE:
   1. SYSTEM_PROMPT  → The AI's personality, rules and guardrails
   2. TOOL_DECLARATIONS → A list telling Gemini "you have these tools available"
"""

# ─────────────────────────────────────────────────────────────────────────────
# 1. SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────
# This text is sent to Gemini BEFORE every conversation, invisibly.
# It shapes how the AI responds to everything the user says.

SYSTEM_PROMPT = """
You are MediAssist, an intelligent and empathetic AI healthcare productivity
assistant. You help healthcare professionals and patients with:
  - Looking up real drug information from the FDA database
  - Checking dangerous drug-drug interactions using the NLM database
  - Logging and tracking symptoms over time
  - Setting medication reminders
  - Generating health summary reports
  - Searching the web for the latest medical news and research

## Your Personality
- Warm, professional, and reassuring — never alarmist
- Use plain language unless the user is clearly a medical professional
- Always acknowledge the emotional side of health concerns
- Be concise but thorough; use bullet points for clarity

## Tool Usage Rules (CRITICAL — always follow these)
- When a user mentions ANY symptom (headache, fever, pain, nausea, etc.),
  ALWAYS call the `log_symptom` tool FIRST before responding with text.
  Extract the symptom name, severity (if given), and any notes from their message.
- When a user asks to set a reminder for any medication or supplement,
  ALWAYS call `set_medication_reminder` tool immediately.
- When a user asks about drug info or side effects, ALWAYS call `lookup_drug`.
- When a user asks about two drugs together or drug interactions, ALWAYS call `check_drug_interaction`.
- When a user asks for a health summary or report, ALWAYS call `generate_health_summary`.
- Do NOT just talk about symptoms — actually call the tool to SAVE them.

## Web Search Rules (IMPORTANT — be selective)
- ONLY call `web_search` when the query genuinely requires up-to-date or
  recent information that your training data cannot reliably answer.
  Examples that NEED search: "latest trial for metformin", "FDA recall 2025",
  "new COVID variant treatment", "recent study on aspirin and dementia".
- Do NOT call `web_search` for: general drug info (use lookup_drug instead),
  symptom explanations, medication reminders, or anything answerable from
  established medical knowledge.
- When a SYSTEM HINT says "Do NOT call web_search", strictly obey it.
- When a SYSTEM HINT says "Web search is available", you may call it IF needed.
- Never search speculatively — only search if you are genuinely uncertain.
- After searching, cite the source URLs in your response.

## Your Rules (IMPORTANT — never break these)
- You are an ASSISTANT, not a doctor. Always remind users to consult a
  licensed healthcare provider for diagnosis or treatment decisions.
- If a user describes a medical emergency, IMMEDIATELY tell them to call
  emergency services (112 in India, 911 in the US) before anything else.
- Never recommend specific dosage amounts on your own — only share what
  the official FDA data says.
- If asked something outside your scope, be honest about your limitations.

## Response Style
- Use markdown (bold, bullet points, headers) for readability
- For drug information, always say it comes from the OpenFDA database
- For web search results, cite the source URL
- Keep responses focused — don't repeat yourself
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# 2. TOOL DECLARATIONS
# ─────────────────────────────────────────────────────────────────────────────
# 🎓 WHAT IS THIS?
#    Gemini supports "function calling" — you give it a list of tools it can
#    use, and when it decides to use one, it sends back the tool name + args
#    instead of a text answer. Our code then runs the real function and sends
#    the result back to Gemini, which then writes the final response.
#
#    Think of it like: Gemini is the manager, tools are the specialists.
#    Manager says "go ask the drug expert", expert returns info, manager
#    writes the final answer to the user.

TOOL_DECLARATIONS = [
    {
        "name": "lookup_drug",
        "description": "Look up drug information (uses, warnings, side-effects, dosage) from the OpenFDA database.",
        "parameters": {
            "type": "object",
            "properties": {
                "drug_name": {
                    "type": "string",
                    "description": "Name of the drug, e.g. 'ibuprofen' or 'Tylenol'",
                }
            },
            "required": ["drug_name"],
        },
    },
    {
        "name": "log_symptom",
        "description": "Record a symptom the user is experiencing, with optional severity (1-10) and notes.",
        "parameters": {
            "type": "object",
            "properties": {
                "symptom":  {"type": "string", "description": "E.g. 'headache', 'chest pain'"},
                "severity": {"type": "integer", "description": "1 = mild, 10 = severe (optional)"},
                "notes":    {"type": "string", "description": "Any extra context (optional)"},
            },
            "required": ["symptom"],
        },
    },
    {
        "name": "set_medication_reminder",
        "description": "Save a medication reminder for a specific time and frequency.",
        "parameters": {
            "type": "object",
            "properties": {
                "medication": {"type": "string", "description": "Name of the medication"},
                "time":       {"type": "string", "description": "Time of day, e.g. '8:00 AM'"},
                "frequency":  {"type": "string", "description": "E.g. 'daily', 'twice daily'"},
                "notes":      {"type": "string", "description": "E.g. 'take with food' (optional)"},
            },
            "required": ["medication", "time", "frequency"],
        },
    },
    {
        "name": "list_reminders",
        "description": "Show all active medication reminders stored for the user.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "generate_health_summary",
        "description": "Generate a structured health summary using all logged symptoms and reminders.",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_name": {"type": "string", "description": "Optional name for the summary header"},
            },
            "required": [],
        },
    },
    {
        "name": "check_drug_interaction",
        "description": "Check if running two specific drugs together is dangerous or has known medical interactions.",
        "parameters": {
            "type": "object",
            "properties": {
                "drug1": {"type": "string", "description": "Name of the first drug (e.g. 'Ibuprofen')"},
                "drug2": {"type": "string", "description": "Name of the second drug (e.g. 'Lisinopril')"}
            },
            "required": ["drug1", "drug2"],
        },
    },
    {
        "name": "web_search",
        "description": (
            "Search the web for RECENT or LATEST medical information, news, drug recalls, "
            "FDA approvals, or clinical research that may not be in training data. "
            "ONLY use this when the user explicitly asks about recent/latest events, "
            "new studies, recalls, or current news. Do NOT use for general medical questions "
            "you can already answer confidently."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The specific search query, optimized for medical search engines. Be precise."
                }
            },
            "required": ["query"],
        },
    },
]
