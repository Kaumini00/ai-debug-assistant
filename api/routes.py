from fastapi import FastAPI
from pydantic import BaseModel
from core.analyzer import analyze_error
from core.agent import run_agent
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

class DebugRequest(BaseModel):
    error: str

class AgentRequest(BaseModel):
    error: str
    codebase_path: str = "."

@app.get("/")
def read_root():
    return {"message": "AI Debug Assistant is running"}

@app.post("/analyze") 
def analyze(request: DebugRequest):
    if not request.error:
        return {"error": "Error message is required"}
    return analyze_error(request.error)

@app.post("/agent/debug")
def agent_debug(request: AgentRequest):
    if not request.error:
        return {"error": "Error message is required"}
    return run_agent(request.error, request.codebase_path)