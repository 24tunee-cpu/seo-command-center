"""
Main API router aggregating all endpoint modules.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    crawler,
    local_radar,
    competitor_intel,
    content_gap,
    backlink_analyzer,
    log_analyzer,
    roi_predictor,
    projects,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(crawler.router, prefix="/crawler", tags=["technical-crawler"])
api_router.include_router(local_radar.router, prefix="/local-radar", tags=["local-seo"])
api_router.include_router(competitor_intel.router, prefix="/competitors", tags=["competitor-intelligence"])
api_router.include_router(content_gap.router, prefix="/content-gap", tags=["nlp-content"])
api_router.include_router(backlink_analyzer.router, prefix="/backlinks", tags=["backlink-analysis"])
api_router.include_router(log_analyzer.router, prefix="/logs", tags=["server-logs"])
api_router.include_router(roi_predictor.router, prefix="/roi", tags=["predictive-analytics"])
