"""
FastAPI application entry point.
Configures middleware, routers, and Beanie ODM initialization.
"""
import contextlib

from beanie import init_beanie
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.models.database import (
    Project,
    CrawlAudit,
    LocalSearchRanking,
    CompetitorSnapshot,
    ContentGapAnalysis,
    BacklinkProfile,
    ServerLogEntry,
    ROIPrediction,
    LeadEvent,
    AIActionCard,
)

# Configure structured logging
configure_logging()

settings = get_settings()


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup/shutdown events.
    """
    # Startup
    client = AsyncIOMotorClient(
        settings.mongodb_uri,
        maxPoolSize=settings.mongodb_max_pool_size
    )
    
    await init_beanie(
        database=client[settings.mongodb_db_name],
        document_models=[
            Project,
            CrawlAudit,
            LocalSearchRanking,
            CompetitorSnapshot,
            ContentGapAnalysis,
            BacklinkProfile,
            ServerLogEntry,
            ROIPrediction,
            LeadEvent,
            AIActionCard,
        ]
    )
    
    app.state.mongo_client = client
    app.state.db = client[settings.mongodb_db_name]
    
    yield
    
    # Shutdown
    client.close()


def create_application() -> FastAPI:
    """
    Factory function to create and configure FastAPI app.
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(api_router, prefix="/api/v1")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": settings.app_version}
    
    return app


app = create_application()
