"""
FastAPI Main Application.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path

from backend.api.routes import router
from backend.config import PROJECT_ROOT
from backend.database.models import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("fall_detection_ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Initializing database...")
    init_db()
    log.info("Database ready.")
    yield
    log.info("Shutting down.")


app = FastAPI(
    title="Fall Detection AI API",
    description="Phát hiện sự kiện té ngã bằng YOLO + Pose + Temporal Analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes FIRST
app.include_router(router, prefix="/api")


@app.get("/api-root")
def api_root():
    return {
        "name": "Fall Detection AI",
        "version": "1.0.0",
        "docs": "/docs",
        "api": "/api",
    }


# Mount static frontend nếu đã build
frontend_dist = PROJECT_ROOT / "frontend" / "dist"
if frontend_dist.exists():
    # Serve assets folder
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        """Catch-all để trả index.html cho client-side routing."""
        # Không handle API ở đây (đã handle ở trên)
        target = frontend_dist / full_path
        if target.exists() and target.is_file():
            return FileResponse(str(target))
        # Fallback index.html cho SPA routing
        return FileResponse(str(frontend_dist / "index.html"))


if __name__ == "__main__":
    import uvicorn
    from backend.config import HOST, PORT
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=False)