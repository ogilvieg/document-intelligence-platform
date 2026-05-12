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
    # Log which DB backend is active — helps diagnose env var issues on Render
    db_url_hint = (settings.rds_database_url[:30] + "...") if settings.rds_database_url else None
    logger.info(
        "application_starting",
        environment=settings.environment,
        debug=settings.debug,
        database_url_set=bool(settings.rds_database_url),
        database_url_preview=db_url_hint,
        supabase_url_set=bool(settings.supabase_url),
    )

    # If using AWS RDS, attempt to open the asyncpg connection pool.
    # Run in background so a slow/failing DB doesn't block port binding.
    if settings.rds_database_url:
        import asyncio
        from app.services.database import get_db_service
        db = get_db_service()
        if hasattr(db, "connect"):
            async def _connect_pool():
                try:
                    await db.connect()
                    logger.info("postgres_pool_ready")
                except Exception as e:
                    logger.error("postgres_pool_failed", error=str(e))
            asyncio.create_task(_connect_pool())
    else:
        logger.warning("database_url_not_set", fallback="supabase")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    # Gracefully close the asyncpg pool if it was opened
    if settings.rds_database_url:
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
