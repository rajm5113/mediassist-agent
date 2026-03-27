"""
tools/drug_lookup.py — Connects to the Official FDA Database

🎓 WHAT THIS TOOL DOES:
   Gemini only knows what it was trained on (which might be outdated).
   If a user asks "What are the side effects of X?", Gemini will call
   this tool. This tool fetches LIVE, official data from the US FDA.

🎓 HOW OPENFDA WORKS:
   It's a free REST API. We send an HTTP GET request using the `requests`
   library. We ask for the "label" data for a specific drug name.
"""

import requests
from typing import Dict, Any

# We import our central config so we don't hardcode the OpenFDA URL here
import config


def lookup_drug(drug_name: str) -> Dict[str, Any]:
    """
    Search OpenFDA for the given drug name and extract only the useful bits.
    """
    # 1. Prepare the API endpoint
    # OpenFDA base URL is: https://api.fda.gov/drug
    url = f"{config.OPENFDA_BASE_URL}/label.json"

    # 2. Set the search parameters
    # We search both "brand_name" (e.g. Tylenol) and "generic_name" (e.g. acetaminophen)
    params = {
        "search": f'openfda.brand_name:"{drug_name}"+openfda.generic_name:"{drug_name}"',
        "limit": 1,  # We just want the single best match
    }

    try:
        # 3. Make the network request
        response = requests.get(url, params=params, timeout=10)

        # 4. Handle a "404 Not Found" gracefully (so the bot doesn't crash)
        if response.status_code == 404:
            return {"error": f"I couldn't find official FDA data for '{drug_name}'."}
            
        # If it's another type of error (like 500 Server Error), raise an exception
        response.raise_for_status()

        # 5. Parse the JSON response
        data = response.json()
        
    except Exception as e:
        # Catch network timeouts or other unexpected errors
        return {"error": f"OpenFDA API error: {str(e)}"}

    # 6. Extract the results
    results = data.get("results", [])
    if not results:
        return {"error": f"No official results found for '{drug_name}'."}

    label = results[0]  # Take the first matched drug label

    # 7. Helper function to safely grab the first paragraph of a field
    def get_first(field_name: str):
        content_list = label.get(field_name, [])
        return content_list[0] if content_list else "Not specified."

    # 8. Return ONLY the information the AI actually needs to answer the user
    # (The raw FDA JSON is massive; we filter it down to save tokens & money)
    return {
        "drug_name": drug_name,
        "source": "Official OpenFDA Database",
        "brand_names": label.get("openfda", {}).get("brand_name", ["Unknown"]),
        "generic_names": label.get("openfda", {}).get("generic_name", ["Unknown"]),
        "purpose": get_first("purpose"),
        "warnings": get_first("warnings"),
        "side_effects": get_first("adverse_reactions"),
        "dosage_info": get_first("dosage_and_administration"),
        "pregnancy_category": get_first("pregnancy_or_breast_feeding"),
    }
