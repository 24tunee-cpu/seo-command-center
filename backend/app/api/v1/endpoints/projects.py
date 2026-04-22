"""
API Endpoints for Project Management.
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.database import Project, AIActionCard, HealthScoreCategory

router = APIRouter()


# ============== REQUEST/RESPONSE MODELS ==============
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    domain: str = Field(..., min_length=3)
    user_id: str
    target_keywords: List[str] = []
    target_locations: List[dict] = []
    competitors: List[str] = []


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    target_keywords: Optional[List[str]] = None
    target_locations: Optional[List[dict]] = None
    competitors: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    domain: str
    user_id: str
    target_keywords: List[str]
    target_locations: List[dict]
    competitors: List[str]
    health_score: float
    health_category: str
    created_at: str
    updated_at: str
    is_active: bool


class AIActionCardResponse(BaseModel):
    id: str
    card_id: str
    title: str
    description: str
    category: str
    severity: str
    estimated_impact: str
    estimated_effort: str
    status: str
    affected_urls: List[str]
    created_at: str


# ============== ENDPOINTS ==============
@router.post("/", response_model=ProjectResponse)
async def create_project(request: ProjectCreate):
    """
    Create a new SEO project.
    """
    # Check if domain already exists for this user
    existing = await Project.find_one(
        Project.domain == request.domain,
        Project.user_id == request.user_id
    )
    
    if existing:
        raise HTTPException(status_code=400, detail="Project for this domain already exists")
    
    project = Project(
        name=request.name,
        domain=request.domain,
        user_id=request.user_id,
        target_keywords=request.target_keywords,
        target_locations=request.target_locations,
        competitors=request.competitors
    )
    
    await project.insert()
    
    return _project_to_response(project)


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(user_id: str):
    """
    List all projects for a user.
    """
    projects = await Project.find(
        Project.user_id == user_id
    ).sort(-Project.created_at).to_list()
    
    return [_project_to_response(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """
    Get project details.
    """
    project = await Project.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return _project_to_response(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, request: ProjectUpdate):
    """
    Update project configuration.
    """
    project = await Project.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if request.name is not None:
        project.name = request.name
    if request.target_keywords is not None:
        project.target_keywords = request.target_keywords
    if request.target_locations is not None:
        project.target_locations = request.target_locations
    if request.competitors is not None:
        project.competitors = request.competitors
    if request.is_active is not None:
        project.is_active = request.is_active
    
    await project.save()
    
    return _project_to_response(project)


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """
    Soft delete a project.
    """
    project = await Project.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.is_active = False
    await project.save()
    
    return {"message": "Project deactivated successfully"}


# ============== AI ACTION CARDS ==============
@router.get("/{project_id}/action-cards", response_model=List[AIActionCardResponse])
async def get_action_cards(
    project_id: str,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 20
):
    """
    Get AI-generated action cards for a project.
    
    Filter by status (pending, swiped_right, completed) or severity.
    """
    query = AIActionCard.find(AIActionCard.project_id == project_id)
    
    if status:
        query = query.find(AIActionCard.status == status)
    if severity:
        query = query.find(AIActionCard.severity == severity)
    
    cards = await query.sort(
        AIActionCard.severity,
        -AIActionCard.created_at
    ).limit(limit).to_list()
    
    return [_card_to_response(c) for c in cards]


@router.post("/{project_id}/action-cards/{card_id}/swipe")
async def swipe_action_card(project_id: str, card_id: str, direction: str):
    """
    Handle swipe action on an AI card.
    
    direction: "left" (dismiss), "right" (accept/complete)
    """
    card = await AIActionCard.find_one(
        AIActionCard.project_id == project_id,
        AIActionCard.card_id == card_id
    )
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    if direction == "right":
        card.status = "swiped_right"
        # In a real implementation, would trigger task creation
    elif direction == "left":
        card.status = "swiped_left"
    elif direction == "complete":
        card.status = "completed"
        from datetime import datetime
        card.completed_at = datetime.utcnow()
    else:
        raise HTTPException(status_code=400, detail="Invalid direction")
    
    await card.save()
    
    return {"message": f"Card swiped {direction}", "card_id": card_id}


# ============== HELPER FUNCTIONS ==============
def _project_to_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        domain=project.domain,
        user_id=project.user_id,
        target_keywords=project.target_keywords,
        target_locations=project.target_locations,
        competitors=project.competitors,
        health_score=project.health_score,
        health_category=project.health_category.value,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
        is_active=project.is_active
    )


def _card_to_response(card: AIActionCard) -> AIActionCardResponse:
    return AIActionCardResponse(
        id=str(card.id),
        card_id=card.card_id,
        title=card.title,
        description=card.description,
        category=card.category,
        severity=card.severity,
        estimated_impact=card.estimated_impact,
        estimated_effort=card.estimated_effort,
        status=card.status,
        affected_urls=card.affected_urls,
        created_at=card.created_at.isoformat()
    )
