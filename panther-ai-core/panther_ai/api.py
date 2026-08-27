from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .tools import TOOL_REGISTRY, run_tool

app = FastAPI(title="Panther AI Core", version="0.1.0")

class ToolRequest(BaseModel):
    arguments: dict = {}

@app.get("/health")
def health():
    return {"status": "ok", "service": "panther-ai-core", "version": "0.1.0"}

@app.get("/tools")
def tools():
    return {"tools": list(TOOL_REGISTRY.values())}

@app.post("/tools/{name}")
def execute_tool(name: str, request: ToolRequest):
    if name not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail="Unknown tool")
    try:
        return run_tool(name, request.arguments)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

def main():
    import uvicorn
    uvicorn.run("panther_ai.api:app", host="127.0.0.1", port=8787)
