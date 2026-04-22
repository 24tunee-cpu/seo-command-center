"""
API Endpoints for Competitor Intelligence.
Real-time monitoring of competitor content and ranking changes.
"""
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

from app.models.database import CompetitorSnapshot, Project, AIActionCard
from app.services.nlp_service import CompetitorIntelligenceService

router = APIRouter()
intel_service = CompetitorIntelligenceService()


# ============== REQUEST/RESPONSE MODELS ==============
class CompetitorMonitorRequest(BaseModel):
    project_id: str
    competitor_domain: str
    keywords: List[str]


class CompetitorSnapshotResponse(BaseModel):
    id: str
    competitor_domain: str
    keyword: str
    position: int
    previous_position: Optional[int]
    position_change: int
    page_title: Optional[str]
    page_url: str
    content_changed: bool
    captured_at: str


# ============== ENDPOINTS ==============
@router.post("/monitor")
async def add_competitor_monitor(request: CompetitorMonitorRequest):
    """
    Add a competitor to the monitoring list for a project.
    """
    project = await Project.get(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Add to project's competitors if not already there
    if request.competitor_domain not in project.competitors:
        project.competitors.append(request.competitor_domain)
        await project.save()
    
    return {
        "message": f"Added {request.competitor_domain} to monitoring",
        "keywords_to_track": len(request.keywords)
    }


@router.get("/snapshots/{project_id}", response_model=List[CompetitorSnapshotResponse])
async def get_competitor_snapshots(
    project_id: str,
    competitor: Optional[str] = None,
    days: int = Query(default=30, le=90)
):
    """
    Get historical competitor snapshots.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = CompetitorSnapshot.find(
        CompetitorSnapshot.project_id == project_id,
        CompetitorSnapshot.captured_at >= cutoff
    )
    
    if competitor:
        query = query.find(CompetitorSnapshot.competitor_domain == competitor)
    
    snapshots = await query.sort(-CompetitorSnapshot.captured_at).limit(200).to_list()
    
    return [_snapshot_to_response(s) for s in snapshots]


@router.get("/changes/{project_id}")
async def detect_competitor_changes(
    project_id: str,
    hours: int = Query(default=24, le=168)
):
    """
    Detect recent content and ranking changes from competitors.
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Find snapshots with changes
    changed = await CompetitorSnapshot.find(
        CompetitorSnapshot.project_id == project_id,
        CompetitorSnapshot.captured_at >= cutoff,
        CompetitorSnapshot.content_changed == True
    ).to_list()
    
    # Find ranking changes
    pipeline = [
        {
            "$match": {
                "project_id": project_id,
                "captured_at": {"$gte": cutoff}
            }
        },
        {
            "$match": {
                "$expr": {"$ne": ["$position", "$previous_position"]}
            }
        }
    ]
    
    ranking_changes = await CompetitorSnapshot.get_motor_collection().aggregate(pipeline).to_list(None)
    
    return {
        "period_hours": hours,
        "content_changes": len(changed),
        "ranking_changes": len(ranking_changes),
        "details": {
            "content_updates": [
                {
                    "competitor": s.competitor_domain,
                    "keyword": s.keyword,
                    "detected_at": s.captured_at.isoformat()
                }
                for s in changed[:10]
            ],
            "ranking_shifts": [
                {
                    "competitor": s["competitor_domain"],
                    "keyword": s["keyword"],
                    "position_change": s.get("position_change", 0),
                    "current_position": s["position"]
                }
                for s in ranking_changes[:10]
            ]
        }
    }


def _snapshot_to_response(snapshot: CompetitorSnapshot) -> CompetitorSnapshotResponse:
    return CompetitorSnapshotResponse(
        id=str(snapshot.id),
        competitor_domain=snapshot.competitor_domain,
        keyword=snapshot.keyword,
        position=snapshot.position,
        previous_position=snapshot.previous_position,
        position_change=snapshot.position_change,
        page_title=snapshot.page_title,
        page_url=snapshot.page_url,
        content_changed=snapshot.content_changed,
        captured_at=snapshot.captured_at.isoformat()
    )
