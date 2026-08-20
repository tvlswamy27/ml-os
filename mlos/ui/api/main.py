from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from .database import engine, Base
from .routers import auth, project

# Create FastAPI application
app = FastAPI(
    title="ML-OS Platform API Engine",
    description="Intelligent Machine Learning Operating System platform layers.",
    version="3.6.0"
)

# Configure CORS with explicit development origins (allowing credentials)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(project.router)


@app.on_event("startup")
def on_startup():
    """Create platform database tables in SQLite on startup."""
    Base.metadata.create_all(bind=engine)


# Mount SPA frontend distribution if built
dist_dir = Path(__file__).resolve().parents[3] / "web" / "dist"
if dist_dir.exists():
    # Mount assets folder
    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Fallback to serve index.html for SPA frontend routing
    @app.get("/{fallback_path:path}")
    def serve_spa_frontend(fallback_path: str):
        if fallback_path.startswith("api/"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API endpoint not found."
            )
        index_file = dist_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Frontend index.html distribution not found."
        )
