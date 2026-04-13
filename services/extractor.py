import json
import re

def parse_llm_output(output):
    try:
        match = re.search(r"\{.*\}", output, re.DOTALL)

        if not match:
            return {"error": "No JSON found"}

        json_str = match.group()
        data = json.loads(json_str)
        return data
    
    except json.JSONDecodeError:
        return {
            "error": "Invalid JSON from LLM"
        }