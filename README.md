# 🤖 AI Debug Assistant

An autonomous debugging agent that analyzes errors, explores your codebase, identifies root causes, and suggests precise fixes powered by LLaMA 3.3 via Groq.

Unlike a simple "paste error -> get answer" tool, this is an **agentic system** that reasons step by step, searches your codebase semantically, and returns a precise patch with `code_before` and `code_after`.

## Documentation
- [API Reference](docs/api-reference.md)

## How it works

```
Error input
    ↓
LLM decides which tools to call
    ↓
vector_search  →  finds semantically related code chunks
read_file      →  reads full file if more context is needed
    ↓
LLM reasons over the retrieved code
    ↓
Returns structured fix with root cause + code patch
```

## Tech Stack

- **[Groq](https://groq.com/)** — LLM inference (LLaMA 3.3 70B)
- **[ChromaDB](https://www.trychroma.com/)** — vector database for semantic code search
- **[Google Gemini](https://ai.google.dev/)** — embeddings (gemini-embedding-001)
- **[FastAPI](https://fastapi.tiangolo.com/)** — API framework
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** — environment variables

## Project Structure

```
ai-debug-assistant/
├── api/
│   └── routes.py            # FastAPI endpoints
├── core/
│   ├── llm.py               # LLM config (Groq/LLaMA)
│   ├── analyzer.py          # Simple error analyzer
│   ├── tool_agent.py        # Agentic loop — LLM drives tool calls
│   └── tools/
│       ├── embedder.py      # Google Gemini embeddings
│       ├── indexer.py       # Chunks + indexes codebase into ChromaDB
│       ├── vector_search.py # Semantic search over indexed codebase
│       └── file_reader.py   # Reads full file contents
├── main.py                  # Starts the server
└── .env
```

## Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/Kaumini00/ai-debug-assistant.git
cd ai-debug-assistant
```

### 2. Create a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the root:
```
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
```

- Groq API key → [console.groq.com](https://console.groq.com)
- Gemini API key → [aistudio.google.com](https://aistudio.google.com)

### 5. Run the server
```bash
python main.py
```

Server runs at `http://localhost:8000`  
Interactive API docs at `http://localhost:8000/docs`

## API Endpoints

### `GET /`
Health check.

### `POST /analyze`
Quick error analysis with no codebase exploration. Good for simple errors.

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

### `POST /agent/index`
Index a codebase for semantic search. Run this once before using `/agent/auto`.  
Re-run whenever your codebase changes significantly.

**Request:**
```json
{
  "codebase_path": "/path/to/your/project"
}
```

**Response:**
```json
{
  "message": "Indexed successfully",
  "chunks": 42
}
```

### `POST /agent/auto`
Full agentic debug. The LLM autonomously decides which tools to call, searches your codebase semantically, and returns a precise fix.

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
  "root_cause": "The 'name' key does not exist in the user dictionary",
  "explanation": "...",
  "affected_file": "app.py",
  "fix": {
    "description": "Use .get() with a default or add the missing key",
    "code_before": "return user['name']",
    "code_after": "return user.get('name', 'Unknown')"
  },
  "additional_notes": "..."
}
```

## Roadmap

- [ ] Frontend (React or Streamlit)
- [ ] GitHub issue input support  
- [ ] Automatic patch application
- [ ] Test runner integration