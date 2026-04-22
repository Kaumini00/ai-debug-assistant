import os
import json
from core.llm import call_llm
from core.tools.file_reader import read_file
from core.tools.code_search import search_code
from dotenv import load_dotenv

load_dotenv()

def list_files(directory: str) -> list:
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith(".py"):
                files.append(os.path.join(root, filename))
    return files

def extract_keywords(error: str) -> list:
    prompt = f"""
Extract the most important keywords from this error for searching a codebase.
Keywords should be function names, variable names, class names, or module names.
STRICT RULES:
- Return ONLY a raw JSON array of strings
- No markdown, no explanation, no backticks
- Example: ["my_function", "user_data"]

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
        print(f"[Agent] Keyword extraction failed: {e}")
        return []

def find_relevant_files(keywords: list, codebase_path: str) -> list:
    relevant = set()
    for keyword in keywords:
        matches = search_code(codebase_path, keyword)
        for match in matches:
            if "file" in match:
                relevant.add(match["file"])
    print(f"[Agent] Found {len(relevant)} relevant file(s): {list(relevant)}")
    return list(relevant)

def generate_fix(error: str, file_contents: dict) -> dict:
    context = ""
    for path, content in file_contents.items():
        context += f"\n\n### File: {path}\n```python\n{content}\n```"

    prompt = f"""
You are an expert debugging assistant with access to the codebase.
Analyze the error and the provided code, then suggest a precise fix.
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

Codebase Context: {context}
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

    print("[Agent] Step 1: Extracting keywords...")
    try:
        keywords = extract_keywords(error)
        print(f"[Agent] Keywords: {keywords}")
    except Exception as e:
        print(f"[Agent] Keyword extraction failed: {e}")
        keywords = []

    print("[Agent] Step 2: Searching codebase...")
    relevant_files = []
    if keywords:
        try:
            relevant_files = find_relevant_files(keywords, codebase_path)
        except Exception as e:
            print(f"[Agent] File search failed: {e}")

    print("[Agent] Step 3: Reading files...")
    file_contents = {}
    for path in relevant_files:
        try:
            file_contents[path] = read_file(path)
        except Exception as e:
            print(f"[Agent] Could not read {path}: {e}")

    print("[Agent] Step 4: Generating fix...")
    try:
        result = generate_fix(error, file_contents)
    except Exception as e:
        result = {"error": "Fix generation failed", "details": str(e)}

    print("[Agent] Done.\n")
    return result