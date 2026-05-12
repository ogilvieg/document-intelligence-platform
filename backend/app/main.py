"""FastAPI main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import structlog

from app.config import settings
from app.models import HealthResponse
from app.api.routes import router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="Document Intelligence Platform API",
    description="AI-powered document intelligence and decision support system",
    version="0.1.0",
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info(
        "application_starting",
        environment=settings.environment,
        debug=settings.debug
    )

    # If using AWS RDS, open the asyncpg connection pool on startup
    if settings.database_url:
        from app.services.database import get_db_service
        db = get_db_service()
        if hasattr(db, "connect"):
            await db.connect()
            logger.info("postgres_pool_ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    # Gracefully close the asyncpg pool if it was opened
    if settings.database_url:
        from app.services.database import get_db_service
        db = get_db_service()
        if hasattr(db, "disconnect"):
            await db.disconnect()
    logger.info("application_shutting_down")


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.utcnow()
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.utcnow()
    )


# Include API routes
app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
