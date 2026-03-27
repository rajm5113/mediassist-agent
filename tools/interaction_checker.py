"""
tools/interaction_checker.py — The Drug Safety Guardian ⚠️

🎓 WHAT IS THIS?
   A new tool for our AI Agent! 
   It hits the US National Library of Medicine (NLM) "RxNav" API to check if 
   taking two drugs together is dangerous.
"""

import json
import requests

def check_drug_interaction(drug1: str, drug2: str) -> str:
    """Checks the NLM API for dangerous interactions between two drugs."""
    try:
        # Step 1: We first must convert the plain English drug names into "RxCUI" codes
        # because the interaction API only understands codes, not names.
        cui1 = _get_rxcui(drug1)
        cui2 = _get_rxcui(drug2)

        if not cui1:
            return json.dumps({"status": "error", "message": f"Could not find FDA code for {drug1}"})
        if not cui2:
            return json.dumps({"status": "error", "message": f"Could not find FDA code for {drug2}"})

        # Step 2: Ask the Interaction API if these two codes have a known conflict
        url = f"https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={cui1}+{cui2}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        # Step 3: Parse the complex API response into a simple summary for the AI
        if "fullInteractionTypeGroup" in data:
            interactions = []
            for group in data["fullInteractionTypeGroup"]:
                for interaction_type in group["fullInteractionType"]:
                    for interaction in interaction_type["interactionPair"]:
                        interactions.append({
                            "description": interaction["description"],
                            "severity": interaction.get("severity", "Unknown")
                        })
            
            return json.dumps({
                "status": "warning_found",
                "drugs": [drug1, drug2],
                "interactions": interactions
            })
        else:
            return json.dumps({
                "status": "safe",
                "message": f"No known dangerous interactions found between {drug1} and {drug2}."
            })

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def _get_rxcui(drug_name: str) -> str:
    """Helper function to fetch the RxCUI ID for a given drug name."""
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={drug_name.replace(' ', '%20')}"
    response = requests.get(url, timeout=5)
    data = response.json()
    
    # If the drug is found, extract its ID
    if "idGroup" in data and "rxnormId" in data["idGroup"]:
        return data["idGroup"]["rxnormId"][0]
    return ""
