from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .tools import TOOL_REGISTRY, run_tool
from .planner import Planner

app = FastAPI(title="Panther AI Core", version="0.2.0")
planner = Planner()

class ToolRequest(BaseModel):
    arguments: dict = {}

class ChatRequest(BaseModel):
    prompt: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "panther-ai-core", "version": "0.2.0"}

@app.get("/tools")
def tools():
    return {"tools": list(TOOL_REGISTRY.values())}

@app.post("/tools/{name}")
def execute_tool(name: str, request: ToolRequest):
    if name not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail="Unknown tool")
    try:
        return run_tool(name, request.arguments)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/chat")
def chat(request: ChatRequest):
    return planner.run(request.prompt)

def main():
    import uvicorn
    uvicorn.run("panther_ai.api:app", host="127.0.0.1", port=8787)
