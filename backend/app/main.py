from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys
from pathlib import Path as PathLib

# Add backend directory to path for imports
backend_dir = PathLib(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.utils.logger import logger
from app.api import users  # Keep users for authentication
from routes import router as main_router  # New consolidated routes

# Removed: certificates, startups (old), jobs (old), cv (old), investments (old)
# All functionality moved to new modules in /backend/cv and /backend/investments

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered CV Builder & Global Job Matching + Diaspora Investment Platform",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)  # Keep for authentication
app.include_router(main_router)  # New consolidated routes for CV and Investments

# Mount static files for photo uploads
static_dir = Path(settings.UPLOAD_DIR).parent
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "TrustBridge API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down TrustBridge API")

