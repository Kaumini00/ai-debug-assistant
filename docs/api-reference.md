# AI Debug Assistant — API Reference

## Overview

The AI Debug Assistant is an autonomous debugging agent that analyzes errors,
semantically searches your codebase, and returns structured fixes with
root cause analysis and code patches.

The agent uses a Retrieval-Augmented Generation (RAG) pipeline: your codebase
is indexed into a vector database, and when an error is submitted, the most
semantically relevant code chunks are retrieved and passed to an LLM for analysis.

**Base URL:** `http://localhost:8000`  
**API Format:** REST  
**Request/Response Format:** JSON  

---

## Authentication

No authentication is required for local deployments. All endpoints are
publicly accessible when running the server locally.

---

## Endpoints

### Health Check

```
GET /
```

Verifies the server is running.

**Response**

| Status | Description |
|--------|-------------|
| `200 OK` | Server is running |

**Example Response**

```json
{
  "message": "AI Debug Assistant is running"
}
```

---

### Analyze Error

```
POST /analyze
```

Performs a quick analysis of an error message without exploring a codebase.
Use this for simple, self-contained errors where codebase context is not needed.

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error` | string | ✅ | The error message or stack trace to analyze |

**Example Request**

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"error": "KeyError: '\''name'\''"}'
```

**Example Response**

```json
{
  "error_type": "KeyError",
  "explanation": "A KeyError occurs when a key does not exist in a dictionary.",
  "possible_causes": [
    "The key 'name' was never added to the dictionary",
    "A typo in the key name — e.g., 'Name' vs 'name'",
    "The dictionary was populated from an external source missing this field"
  ],
  "fixes": [
    "Use dict.get('name', default) to avoid raising an error",
    "Verify the dictionary keys with dict.keys() before accessing",
    "Add a check: if 'name' in my_dict before accessing"
  ]
}
```

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `error_type` | string | Classified error type |
| `explanation` | string | Plain-language explanation of the error |
| `possible_causes` | array of strings | List of likely root causes |
| `fixes` | array of strings | Suggested fixes |

---

### Index Codebase

```
POST /agent/index
```

Indexes a codebase for semantic search. This must be called before using
`/agent/auto` on a new codebase. The indexer walks all `.py` files,
splits them into chunks, generates vector embeddings, and stores them
in ChromaDB.

Re-index whenever the codebase changes significantly.

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `codebase_path` | string | ✅ | Absolute path to the codebase directory |

**Example Request**

```bash
curl -X POST http://localhost:8000/agent/index \
  -H "Content-Type: application/json" \
  -d '{"codebase_path": "/home/user/my-project"}'
```

**Example Response**

```json
{
  "message": "Indexed successfully",
  "chunks": 42
}
```

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Confirmation message |
| `chunks` | integer | Number of code chunks indexed |

**Notes**
- Skips `.venv/`, `__pycache__/`, `.git/`, and `node_modules/` automatically
- Only indexes `.py` files in the current version
- Existing index is cleared and rebuilt on each call

---

### Auto Debug (Agentic)

```
POST /agent/auto
```

Submits an error for full agentic debugging. The LLM autonomously decides
which tools to call — it may search the codebase multiple times with
refined queries, read specific files for deeper context, or trigger
indexing if the codebase has not been indexed yet.

Returns a structured fix with root cause analysis and a before/after code patch.

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error` | string | ✅ | The error message or stack trace |
| `codebase_path` | string | ✅ | Absolute path to the indexed codebase |

**Example Request**

```bash
curl -X POST http://localhost:8000/agent/auto \
  -H "Content-Type: application/json" \
  -d '{
    "error": "KeyError: '\''name'\''",
    "codebase_path": "/home/user/my-project"
  }'
```

**Example Response**

```json
{
  "error_type": "KeyError",
  "root_cause": "The 'name' key does not exist in the user dictionary. The dictionary only contains 'username' and 'age'.",
  "explanation": "The get_user function accesses user['name'], but the dictionary is populated with 'username' as the key, not 'name'.",
  "affected_file": "app.py",
  "fix": {
    "description": "Replace the direct key access with the correct key name, or use .get() for safe access.",
    "code_before": "return user['name']",
    "code_after": "return user.get('username', 'Unknown')"
  },
  "additional_notes": "Consider using .get() throughout the codebase to prevent similar KeyErrors when dictionary keys are uncertain."
}
```

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `error_type` | string | Classified error type |
| `root_cause` | string | Precise root cause identified from the codebase |
| `explanation` | string | Detailed explanation of why the error occurs |
| `affected_file` | string | The file where the bug was found |
| `fix.description` | string | Plain-language description of the fix |
| `fix.code_before` | string | The buggy code snippet |
| `fix.code_after` | string | The corrected code snippet |
| `additional_notes` | string | Optional broader recommendations |

**Notes**
- Index the codebase with `/agent/index` before calling this endpoint
- The agent may take 10–30 seconds depending on codebase size and LLM response time
- The agent loop runs a maximum of 10 iterations to prevent infinite loops

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "error": "Description of what went wrong",
  "details": "Additional technical detail"
}
```

**Common errors**

| Error | Cause |
|-------|-------|
| `"Error message is required"` | Empty `error` field in request |
| `"Codebase not indexed yet"` | Called `/agent/auto` before `/agent/index` |
| `"Fix generation failed"` | LLM API error or rate limit hit |

---

## Quickstart

```bash
# 1. Start the server
python main.py

# 2. Index your project
curl -X POST http://localhost:8000/agent/index \
  -H "Content-Type: application/json" \
  -d '{"codebase_path": "/path/to/your/project"}'

# 3. Debug an error
curl -X POST http://localhost:8000/agent/auto \
  -H "Content-Type: application/json" \
  -d '{
    "error": "KeyError: '\''name'\''",
    "codebase_path": "/path/to/your/project"
  }'
```

Or use the interactive docs at `http://localhost:8000/docs`