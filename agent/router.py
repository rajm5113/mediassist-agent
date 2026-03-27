"""
agent/router.py — The Tool Dispatcher

🎓 WHAT IS THIS?
   When Gemini decides it needs a tool, it sends back a message saying:
   "Call tool 'lookup_drug' with arg {'drug_name': 'ibuprofen'}"
   
   Gemini CANNOT run Python code. It is just text. 
   So we need a "Router" (a traffic cop) that looks at the string 
   'lookup_drug', imports our actual Python function from the /tools 
   folder, runs it, and turns the dictionary result into a JSON string 
   to send *back* to Gemini.
"""

import json
from typing import Any, Dict

# Import all our specialist tools
from tools.drug_lookup import lookup_drug
from tools.symptom_logger import log_symptom
from tools.medication_reminder import set_medication_reminder, list_reminders
from tools.health_summary import generate_health_summary
from tools.interaction_checker import check_drug_interaction


def route_tool_call(function_name: str, function_args: Dict[str, Any]) -> str:
    """
    Acts as the middleman between Gemini's request and our Python code.
    Returns a JSON-formatted string of the result.
    """
    try:
        if function_name == "lookup_drug":
            # Pass the drug_name argument to our function
            result = lookup_drug(function_args["drug_name"])

        elif function_name == "check_drug_interaction":
            result = check_drug_interaction(
                drug1=function_args["drug1"],
                drug2=function_args["drug2"]
            )

        elif function_name == "log_symptom":
            # Pass symptom, severity, and notes
            result = log_symptom(
                symptom=function_args["symptom"],
                severity=function_args.get("severity"),
                notes=function_args.get("notes")
            )

        elif function_name == "set_medication_reminder":
            result = set_medication_reminder(
                medication=function_args["medication"],
                time=function_args["time"],
                frequency=function_args["frequency"],
                notes=function_args.get("notes")
            )

        elif function_name == "list_reminders":
            # This tool takes no arguments
            result = list_reminders()

        elif function_name == "generate_health_summary":
            # patient_name is optional
            result = generate_health_summary(
                patient_name=function_args.get("patient_name", "User")
            )

        else:
            # If Gemini somehow hallucinates a tool that doesn't exist
            result = {"error": f"I don't know how to use the tool: {function_name}"}

    except Exception as exc:
        # If our Python code crashes, don't crash the bot. Just tell Gemini what went wrong.
        result = {"error": f"Tool execution failed: {str(exc)}"}

    # Gemini requires the final result to be a string, not a Python dictionary
    return json.dumps(result, ensure_ascii=False, indent=2)
