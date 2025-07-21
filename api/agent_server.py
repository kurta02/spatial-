"""
FastAPI Agent Server for File Operations

This server provides HTTP endpoints for file operations used by agent systems.
"""

from fastapi import FastAPI, Request, HTTPException
import os
import logging

app = FastAPI(title="Agent File Operations Server")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/read_file")
async def read_file(request: Request):
    """Read file content via HTTP API"""
    try:
        data = await request.json()
        path = data.get("path")
        logger.info(f"📥 Requested path: {path}")

        if not os.path.isfile(path):
            logger.error(f"❌ File not found: {path}")
            raise HTTPException(status_code=404, detail="File not found")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        logger.error(f"❌ Exception in /read_file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/write_file")
async def write_file(request: Request):
    """Write file content via HTTP API"""
    try:
        data = await request.json()
        path = data.get("path")
        content = data.get("content")
        logger.info(f"💾 Writing to: {path}")

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"❌ Exception in /write_file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agent_server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)