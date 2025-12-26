import traceback

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from src.backend.auth import verify_token
from src.backend.routers import auth, processes, programs, servers, sync, tools
from src.backend.services.logging import logger
from src.backend.settings import get_settings


app = FastAPI(title="MCPZoo", version="0.1.0", debug=True)

# Custom exception handler for detailed error logging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log full stack traces for all exceptions."""
    logger.error(f"Unhandled exception in {request.method} {request.url}: {exc}")
    logger.error(f"Full traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "traceback": traceback.format_exc(),
            "path": str(request.url),
            "method": request.method
        }
    )

# CORS middleware - Allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(servers.router)
app.include_router(programs.router)
app.include_router(processes.router)
app.include_router(sync.router)
app.include_router(tools.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/home")
async def home(username: Optional[str] = None):
    """Home page metadata with installed servers summary and statuses.

    Returns:
        - Total servers installed
        - Total processes running
        - Servers list with current status
        - Process statuses
    """
    logger.info("Home endpoint called")
    try:
        from src.backend.services.supervisord import supervisord_service
        from src.backend.tinydb import db

        logger.debug("Getting servers from database...")
        servers_list = db.get_all_servers()
        logger.debug(f"Found {len(servers_list)} servers")

        logger.debug("Getting programs from supervisord...")
        programs = await supervisord_service.get_all_programs()
        logger.debug(f"Found {len(programs)} programs")

        running_count = sum(1 for p in programs if p.process and p.process.state.value == "RUNNING")
        logger.info(f"Home endpoint returning {len(servers_list)} servers, {running_count} running processes")

        return {
            "name": "MCPZoo",
            "version": "0.1.0",
            "description": "MCP Server Management",
            "summary": {
                "total_servers": len(servers_list),
                "running_processes": running_count,
                "total_processes": len(programs),
            },
            "servers": servers_list,
            "processes": [p.model_dump() for p in programs],
        }
    except Exception as e:
        logger.error(f"Error in home endpoint: {str(e)}")
        raise


# Serve static files from frontend/dist
static_path = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")



settings = get_settings()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=settings.backend_web_port)
