import json
import re

def parse_llm_output(output):
    try:
        if not isinstance(output, str):
            return {"error": "Output is not a string"}

        cleaned = output.strip()
        cleaned = re.sub(r"^```json\s*|```$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)

        if not match:
            return {"error": "No JSON found"}

        json_str = match.group()
        data = json.loads(json_str)
        return data
    
    except json.JSONDecodeError:
        return {
            "error": "Invalid JSON from LLM"
        }