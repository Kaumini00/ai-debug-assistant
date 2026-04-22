# 🤖 AI Debug Assistant

An autonomous debugging agent that analyzes errors, explores your codebase, identifies root causes, and suggests precise fixes powered by LLaMA 3.3 via Groq.

## API Endpoints

### `GET /`
Health check.

### `POST /analyze`
Simple error analysis. No codebase exploration.

**Request:**
```json
{
  "error": "KeyError: 'name'"
}
```

**Response:**
```json
{
  "error_type": "KeyError",
  "explanation": "...",
  "possible_causes": ["..."],
  "fixes": ["..."]
}
```

### `POST /agent/debug`
Full agentic debug. Explores your codebase and returns a precise fix.

**Request:**
```json
{
  "error": "KeyError: 'name'",
  "codebase_path": "/path/to/your/project"
}
```

**Response:**
```json
{
  "error_type": "KeyError",
  "root_cause": "...",
  "explanation": "...",
  "affected_file": "app.py",
  "fix": {
    "description": "...",
    "code_before": "user['name']",
    "code_after": "user.get('name', 'Unknown')"
  },
  "additional_notes": "..."
}
```
