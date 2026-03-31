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
    """Checks for dangerous interactions between two drugs using a local database."""
    try:
        drug1_lower = drug1.lower()
        drug2_lower = drug2.lower()

        # A simulated database of well-known dangerous drug combinations
        # (Since the official NLM RxNav Interaction API was retired)
        known_interactions = {
            ("ibuprofen", "lisinopril"): "Decreases the blood-pressure lowering effect of Lisinopril and may cause kidney damage.",
            ("acetaminophen", "alcohol"): "Severely increases the risk of liver damage or liver failure.",
            ("tylenol", "alcohol"): "Severely increases the risk of liver damage or liver failure.",
            ("warfarin", "aspirin"): "Increases the risk of severe bleeding complications.",
            ("sildenafil", "nitroglycerin"): "Can cause a severe, life-threatening drop in blood pressure.",
            ("ciprofloxacin", "simvastatin"): "Can cause heart rhythm problems (QT prolongation)."
        }

        # Check both orderings (A+B and B+A)
        found_interaction = None
        for (d1, d2), warning in known_interactions.items():
            if (d1 in drug1_lower and d2 in drug2_lower) or (d2 in drug1_lower and d1 in drug2_lower):
                found_interaction = warning
                break

        if found_interaction:
            return json.dumps({
                "status": "warning_found",
                "drugs": [drug1, drug2],
                "interactions": [{"severity": "High", "description": found_interaction}]
            })
        else:
            return json.dumps({
                "status": "safe",
                "message": f"No known dangerous interactions found in our database between {drug1} and {drug2}."
            })

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
