"""
API Endpoints for Technical SEO Crawler.
Provides single URL audit and full site crawl capabilities.
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, HttpUrl

from app.models.database import CrawlAudit, Project, CrawlStatus
from app.services.crawler_service import TechnicalCrawler

router = APIRouter()
crawler = TechnicalCrawler()


# ============== REQUEST/RESPONSE MODELS ==============
class SingleUrlAuditRequest(BaseModel):
    url: HttpUrl
    project_id: str
    check_pagespeed: bool = True


class SiteCrawlRequest(BaseModel):
    start_url: HttpUrl
    project_id: str
    max_pages: int = Query(default=100, le=500)
    max_depth: int = Query(default=3, le=5)


class AuditResponse(BaseModel):
    id: str
    url: str
    status: CrawlStatus
    status_code: Optional[int]
    title: Optional[str]
    title_length: Optional[int]
    meta_description: Optional[str]
    core_web_vitals_score: Optional[int]
    issue_counts: dict
    word_count: Optional[int]
    crawled_at: str


class AuditDetailResponse(AuditResponse):
    headings: dict
    schema_markup: List[dict]
    images_without_alt: List[dict]
    internal_links_count: int
    external_links_count: int
    issues: List[dict]


# ============== ENDPOINTS ==============
@router.post("/audit-url", response_model=AuditResponse)
async def audit_single_url(
    request: SingleUrlAuditRequest,
    background_tasks: BackgroundTasks
):
    """
    Perform comprehensive technical audit on a single URL.
    
    Analyzes:
    - Core Web Vitals (via PageSpeed API)
    - Title and meta description optimization
    - Heading hierarchy (H1-H6)
    - Schema markup validation
    - Image alt text completeness
    - Internal/external link structure
    """
    import uuid
    crawl_session_id = str(uuid.uuid4())
    
    audit = await crawler.crawl_url(
        url=str(request.url),
        project_id=request.project_id,
        crawl_session_id=crawl_session_id,
        check_pagespeed=request.check_pagespeed
    )
    
    return _audit_to_response(audit)


@router.post("/crawl-site")
async def crawl_entire_site(request: SiteCrawlRequest):
    """
    Multi-page site crawl with BFS traversal.
    
    Crawls up to max_pages starting from start_url,
    following internal links up to max_depth levels.
    """
    # Verify project exists
    project = await Project.get(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    results = await crawler.crawl_site(
        start_url=str(request.start_url),
        project_id=request.project_id,
        max_pages=request.max_pages,
        max_depth=request.max_depth
    )
    
    return {
        "crawl_session_id": results[0].crawl_session_id if results else None,
        "total_pages": len(results),
        "successful": len([r for r in results if r.status == CrawlStatus.COMPLETED]),
        "failed": len([r for r in results if r.status == CrawlStatus.FAILED]),
        "audits": [_audit_to_response(r) for r in results]
    }


@router.get("/audits/{project_id}", response_model=List[AuditResponse])
async def get_project_audits(
    project_id: str,
    limit: int = Query(default=50, le=100),
    skip: int = 0
):
    """
    Retrieve paginated crawl audits for a project.
    Sorted by most recent first.
    """
    audits = await CrawlAudit.find(
        CrawlAudit.project_id == project_id
    ).sort(-CrawlAudit.crawled_at).skip(skip).limit(limit).to_list()
    
    return [_audit_to_response(audit) for audit in audits]


@router.get("/audit/{audit_id}", response_model=AuditDetailResponse)
async def get_audit_details(audit_id: str):
    """
    Get detailed information for a specific audit.
    Includes full heading hierarchy, schema markup, and all detected issues.
    """
    from beanie import PydanticObjectId
    
    try:
        audit = await CrawlAudit.get(PydanticObjectId(audit_id))
    except:
        audit = None
    
    if not audit:
        # Try finding by internal ID if stored
        audit = await CrawlAudit.find_one({"_id": audit_id})
    
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    return _audit_to_detail_response(audit)


@router.get("/health-score/{project_id}")
async def get_project_health_score(project_id: str):
    """
    Calculate overall project health score based on latest audits.
    
    Health Score Formula:
    - Core Web Vitals: 30%
    - On-Page SEO: 25%
    - Technical Issues: 25%
    - Content Quality: 20%
    """
    # Get recent audits for the project
    audits = await CrawlAudit.find(
        CrawlAudit.project_id == project_id,
        CrawlAudit.status == CrawlStatus.COMPLETED
    ).sort(-CrawlAudit.crawled_at).limit(50).to_list()
    
    if not audits:
        return {
            "health_score": 0,
            "category": "poor",
            "message": "No completed audits found for this project"
        }
    
    # Calculate weighted health score
    total_pages = len(audits)
    
    # CWV Score (30%)
    cwv_scores = [
        a.core_web_vitals.score_mobile or 0 
        for a in audits 
        if a.core_web_vitals and a.core_web_vitals.score_mobile
    ]
    avg_cwv = sum(cwv_scores) / len(cwv_scores) if cwv_scores else 50
    
    # On-page score (25%) - based on title/desc presence
    on_page_issues = sum(
        a.issue_counts.get("critical", 0) * 10 + 
        a.issue_counts.get("high", 0) * 5
        for a in audits
    )
    on_page_score = max(0, 100 - (on_page_issues / total_pages) * 2)
    
    # Technical score (25%) - broken links, schema, etc
    technical_issues = sum(
        a.issue_counts.get("medium", 0)
        for a in audits
    )
    technical_score = max(0, 100 - (technical_issues / total_pages) * 3)
    
    # Content score (20%) - word count, readability
    content_scores = []
    for a in audits:
        score = 0
        if a.word_count and a.word_count >= 500:
            score += 50
        elif a.word_count and a.word_count >= 300:
            score += 30
        if not a.images_without_alt:
            score += 50
        content_scores.append(score)
    avg_content = sum(content_scores) / len(content_scores) if content_scores else 40
    
    # Weighted average
    health_score = (
        avg_cwv * 0.30 +
        on_page_score * 0.25 +
        technical_score * 0.25 +
        avg_content * 0.20
    )
    
    # Determine category
    if health_score >= 90:
        category = "excellent"
    elif health_score >= 70:
        category = "good"
    elif health_score >= 50:
        category = "needs_work"
    else:
        category = "poor"
    
    return {
        "health_score": round(health_score, 1),
        "category": category,
        "breakdown": {
            "core_web_vitals": round(avg_cwv, 1),
            "on_page_seo": round(on_page_score, 1),
            "technical": round(technical_score, 1),
            "content": round(avg_content, 1)
        },
        "pages_analyzed": total_pages,
        "total_issues": sum(
            sum(a.issue_counts.values()) for a in audits
        )
    }


# ============== HELPER FUNCTIONS ==============
def _audit_to_response(audit: CrawlAudit) -> AuditResponse:
    """Convert CrawlAudit to response model."""
    return AuditResponse(
        id=str(audit.id),
        url=audit.url,
        status=audit.status,
        status_code=audit.status_code,
        title=audit.title,
        title_length=audit.title_length,
        meta_description=audit.meta_description,
        core_web_vitals_score=audit.core_web_vitals.score_mobile if audit.core_web_vitals else None,
        issue_counts=audit.issue_counts,
        word_count=audit.word_count,
        crawled_at=audit.crawled_at.isoformat()
    )


def _audit_to_detail_response(audit: CrawlAudit) -> AuditDetailResponse:
    """Convert CrawlAudit to detailed response model."""
    base = _audit_to_response(audit)
    return AuditDetailResponse(
        **base.dict(),
        headings=audit.headings.dict() if audit.headings else {},
        schema_markup=[s.dict() for s in audit.schema_markup],
        images_without_alt=[img.dict() for img in audit.images_without_alt],
        internal_links_count=len(audit.internal_links),
        external_links_count=len(audit.external_links),
        issues=[issue.dict() for issue in audit.issues]
    )
