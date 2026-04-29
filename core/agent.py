import json
import os
from groq import Groq
from core.tools.vector_search import vector_search
from core.tools.file_reader import read_file
from core.tools.indexer import index_codebase
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── Tool definitions ──
# Decide which tool to call and what arguments to pass

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "vector_search",
            "description": "Semantically search the codebase for code related to an error. Always call this first when debugging an error.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The error message or description to search for"
                    },
                    "codebase_path": {
                        "type": "string",
                        "description": "Path to the codebase to search"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return. Default is 5.",
                    }
                },
                "required": ["query", "codebase_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full contents of a specific file. Use this after vector_search when you need more context around a specific file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Full path to the file to read"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "index_codebase",
            "description": "Index a codebase for semantic search. Call this only if vector_search returns no results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "codebase_path": {
                        "type": "string",
                        "description": "Path to the codebase to index"
                    }
                },
                "required": ["codebase_path"]
            }
        }
    }
]

# ── Tool executor ──

def execute_tool(name: str, arguments: dict) -> str:
    print(f"[Tool Agent] → Calling tool: {name}")
    print(f"[Tool Agent]   Args: {arguments}")

    if name == "vector_search":
        result = vector_search(
            codebase_path=arguments["codebase_path"],
            query=arguments["query"],
            top_k=arguments.get("top_k", 5)
        )
        return json.dumps(result, indent=2)

    elif name == "read_file":
        return read_file(arguments["path"])

    elif name == "index_codebase":
        count = index_codebase(arguments["codebase_path"])
        return json.dumps({"indexed_chunks": count})

    else:
        return json.dumps({"error": f"Unknown tool: {name}"})

# ── Agent loop ──

def run_tool_agent(error: str, codebase_path: str = ".") -> dict:
    print(f"\n[Tool Agent] Starting...")

    # Conversation history
    messages = [
        {
            "role": "system",
            "content": f"""You are an expert debugging assistant.
You have tools to search and read a codebase at: {codebase_path}

When given an error:
1. ALWAYS call vector_search first to find relevant code
2. Call read_file if you need more context on a specific file
3. Once you have enough context, return your final answer

Your final answer MUST be ONLY this raw JSON with no markdown, no backticks:
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
}}"""
        },
        {
            "role": "user",
            "content": f"Debug this error:\n\n{error}"
        }
    ]

    max_iterations = 10     # prevents infinite loops
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"\n[Tool Agent] Iteration {iteration}...")

        # Ask LLM what to do next
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",     # LLM decides: call a tool OR give final answer
            temperature=0.2
        )

        message = response.choices[0].message

        # ── Case 1: LLM wants to call a tool ──
        if message.tool_calls:

            # Add LLM's decision to history
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            # Execute each tool the LLM requested
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                tool_result = execute_tool(tool_name, tool_args)

                # Add tool result to history so LLM can see it next iteration
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })

        # ── Case 2: LLM is done - parse final answer ───
        else:
            print("[Tool Agent] LLM finished. Parsing final answer...")
            try:
                text = message.content.strip()

                # Clean markdown if LLM ignored instructions
                if text.startswith("```"):
                    lines = text.split("\n")[1:]
                    if lines[-1].strip() == "```":
                        lines = lines[:-1]
                    text = "\n".join(lines).strip()

                return json.loads(text)

            except Exception as e:
                return {
                    "error": "Failed to parse final answer",
                    "details": str(e),
                    "raw": message.content
                }

    # Reached max iterations without finishing
    return {"error": "Agent reached max iterations without a final answer"}