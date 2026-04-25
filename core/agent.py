import os
import json
from core.llm import call_llm
from core.tools.vector_search import vector_search  
from dotenv import load_dotenv

load_dotenv()

def generate_fix(error: str, chunks: list) -> dict:
    # Build context from chunks instead of full files
    context = ""
    for match in chunks:
        if "error" in match:
            continue
        context += f"\n\n### File: {match['file']} (lines {match['start_line']}-{match['end_line']})\n"
        context += f"```python\n{match['chunk']}\n```"

    prompt = f"""
You are an expert debugging assistant with access to relevant parts of the codebase.
Analyze the error and the provided code chunks, then suggest a precise fix.
STRICT RULES:
- Return ONLY raw JSON
- No markdown, no backticks, no explanation outside JSON
Format:
{{
  "error_type": "",
  "root_cause": "",
  "explanation": "",
  "affected_file": "",
  "fix": {{
    "description": "",
    "code_before": "",
    "code_after": ""
  }},
  "additional_notes": ""
}}

Error: {error}

Relevant Code:
{context}
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
        return {"error": "Fix generation failed", "details": str(e)}

def run_agent(error: str, codebase_path: str = ".") -> dict:
    print(f"\n[Agent] Starting...")

    print("[Agent] Step 1: Searching codebase semantically...")
    try:
        chunks = vector_search(codebase_path, error, top_k=5)
        print(f"[Agent] Found {len(chunks)} relevant chunks")
        for c in chunks:
            if "file" in c:
                print(f"  → {c['file']} (lines {c['start_line']}-{c['end_line']}) score: {c['similarity_score']}")
    except Exception as e:
        print(f"[Agent] Vector search failed: {e}")
        chunks = []

    print("[Agent] Step 2: Generating fix...")
    try:
        result = generate_fix(error, chunks)
    except Exception as e:
        result = {"error": "Fix generation failed", "details": str(e)}

    print("[Agent] Done.\n")
    return result