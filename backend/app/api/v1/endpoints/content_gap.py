"""
API Endpoints for NLP Content Gap Analysis.
"""
from typing import List

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.models.database import ContentGapAnalysis, Project
from app.services.nlp_service import NLPContentAnalyzer

router = APIRouter()
nlp_service = NLPContentAnalyzer()


# ============== REQUEST/RESPONSE MODELS ==============
class ContentGapRequest(BaseModel):
    project_id: str
    target_keyword: str
    target_url: str
    competitor_urls: List[str]


class LSIKeywordItem(BaseModel):
    keyword: str
    relevance_score: float
    competitor_usage: str
    frequency_in_competitors: int


class TopicCluster(BaseModel):
    topic: str
    related_terms: List[dict]
    present_in_target: bool
    frequency: int


class ContentGapResponse(BaseModel):
    id: str
    target_keyword: str
    missing_lsi_keywords: List[LSIKeywordItem]
    topic_clusters: List[TopicCluster]
    entities_present: List[str]
    suggested_word_count: int
    suggested_headings: List[str]
    analyzed_at: str


# ============== ENDPOINTS ==============
@router.post("/analyze", response_model=ContentGapResponse)
async def analyze_content_gap(request: ContentGapRequest):
    """
    Analyze content gaps between target page and competitors.
    
    Extracts LSI keywords, identifies missing topics, and provides
    semantic content recommendations.
    """
    # Verify project exists
    project = await Project.get(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Perform analysis
    analysis = await nlp_service.analyze_content_gap(
        project_id=request.project_id,
        target_keyword=request.target_keyword,
        target_url=request.target_url,
        competitor_urls=request.competitor_urls
    )
    
    return _analysis_to_response(analysis)


@router.get("/analyses/{project_id}", response_model=List[ContentGapResponse])
async def get_project_analyses(
    project_id: str,
    limit: int = 20
):
    """
    Retrieve all content gap analyses for a project.
    """
    analyses = await ContentGapAnalysis.find(
        ContentGapAnalysis.project_id == project_id
    ).sort(-ContentGapAnalysis.analyzed_at).limit(limit).to_list()
    
    return [_analysis_to_response(a) for a in analyses]


@router.get("/missing-keywords/{project_id}")
async def get_top_missing_keywords(
    project_id: str,
    target_keyword: str,
    limit: int = 30
):
    """
    Get prioritized list of missing keywords for quick action.
    Sorted by relevance score and competitor usage.
    """
    analysis = await ContentGapAnalysis.find_one(
        ContentGapAnalysis.project_id == project_id,
        ContentGapAnalysis.target_keyword == target_keyword
    ).sort(-ContentGapAnalysis.analyzed_at)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "target_keyword": target_keyword,
        "total_missing": len(analysis.missing_lsi_keywords),
        "top_keywords": analysis.missing_lsi_keywords[:limit]
    }


@router.post("/compare-pages")
async def compare_two_pages(url1: str, url2: str):
    """
    Direct comparison between two pages for semantic similarity.
    """
    try:
        content1 = await nlp_service._fetch_content(url1)
        content2 = await nlp_service._fetch_content(url2)
        
        similarity = nlp_service.calculate_semantic_similarity(content1, content2)
        
        terms1 = set(nlp_service._extract_terms(content1).keys())
        terms2 = set(nlp_service._extract_terms(content2).keys())
        
        unique_to_1 = list(terms1 - terms2)[:20]
        unique_to_2 = list(terms2 - terms1)[:20]
        
        return {
            "semantic_similarity": round(similarity, 3),
            "url1_unique_terms": unique_to_1,
            "url2_unique_terms": unique_to_2,
            "common_terms": list(terms1 & terms2)[:30]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== HELPER FUNCTIONS ==============
def _analysis_to_response(analysis: ContentGapAnalysis) -> ContentGapResponse:
    """Convert ContentGapAnalysis to response model."""
    return ContentGapResponse(
        id=str(analysis.id),
        target_keyword=analysis.target_keyword,
        missing_lsi_keywords=analysis.missing_lsi_keywords,
        topic_clusters=analysis.topic_clusters,
        entities_present=analysis.entities_present,
        suggested_word_count=analysis.suggested_word_count or 1500,
        suggested_headings=analysis.suggested_headings,
        analyzed_at=analysis.analyzed_at.isoformat()
    )
