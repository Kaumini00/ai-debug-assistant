import json
from core.llm import call_llm

def analyze_error(error):
    prompt = f"""
You are an expert debugging assistant.
Analyze the following error and suggest fixes.
STRICT RULES:
- Return ONLY raw JSON
- Do NOT wrap in markdown (no ``` or ```json)
- Do NOT include explanations outside JSON
- Output must be directly parsable by json.loads()
Format:
{{
  "error_type": "",
  "explanation": "",
  "possible_causes": [],
  "fixes": []
}}

Error: {error}
"""
    try:
        text = call_llm(prompt)
        if text.startswith("```"):
            lines = text.split("\n")[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return json.loads(text)
    except Exception as e:
        return {"error": "LLM Error", "details": str(e)}