"""
MongoDB Beanie Document Models for time-series SEO data storage.
All models use indexed fields for optimal query performance.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from beanie import Document, Indexed, Link, before_event, Replace, Insert
from pydantic import BaseModel, Field


# ============== ENUMS ==============
class CrawlStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class HealthScoreCategory(str, Enum):
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"            # 70-89
    NEEDS_WORK = "needs_work" # 50-69
    POOR = "poor"            # 0-49


# ============== SUBMODELS ==============
class CoreWebVitals(BaseModel):
    lcp: Optional[float] = None  # Largest Contentful Paint (seconds)
    fid: Optional[int] = None    # First Input Delay (milliseconds)
    cls: Optional[float] = None  # Cumulative Layout Shift
    fcp: Optional[float] = None  # First Contentful Paint
    ttfb: Optional[float] = None  # Time to First Byte
    score_mobile: Optional[int] = None
    score_desktop: Optional[int] = None


class HeadingHierarchy(BaseModel):
    h1: List[str] = []
    h2: List[str] = []
    h3: List[str] = []
    h4: List[str] = []
    h5: List[str] = []
    h6: List[str] = []
    issues: List[str] = []


class SchemaMarkup(BaseModel):
    type: str
    properties: Dict[str, Any] = {}
    valid: bool = True
    errors: List[str] = []


class ImageAltIssue(BaseModel):
    src: str
    severity: IssueSeverity
    suggestion: str


class PageIssue(BaseModel):
    type: str
    severity: IssueSeverity
    description: str
    element: Optional[str] = None
    line_number: Optional[int] = None
    fix_suggestion: str


class InternalLink(BaseModel):
    source_url: str
    target_url: str
    anchor_text: str
    is_broken: bool = False
    status_code: Optional[int] = None


class LocalRanking(BaseModel):
    position: int
    coordinates: Dict[str, float]  # {lat: float, lng: float}
    distance_km: float
    search_radius: int  # meters
    timestamp: datetime


class CompetitorChange(BaseModel):
    competitor_domain: str
    change_type: str  # "new_content", "ranking_drop", "ranking_gain"
    previous_position: Optional[int] = None
    current_position: Optional[int] = None
    detected_at: datetime
    details: Dict[str, Any] = {}


class BacklinkMetrics(BaseModel):
    domain_authority: Optional[int] = None
    trust_flow: Optional[int] = None
    citation_flow: Optional[int] = None
    toxic_score: float = 0.0
    is_dofollow: bool = True
    first_seen: datetime
    last_checked: datetime


# ============== MAIN DOCUMENTS ==============
class Project(Document):
    """
    Central project configuration.
    Each client/workspace has one project document.
    """
    name: Indexed(str) = Field(..., description="Project name")
    domain: Indexed(str) = Field(..., description="Primary domain")
    user_id: Indexed(str) = Field(..., description="Owner user ID")
    
    # Configuration
    target_keywords: List[str] = []
    target_locations: List[Dict[str, Any]] = []  # {city, country, lat, lng}
    competitors: List[str] = []  # Competitor domains
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    # Aggregated Health Score (0-100)
    health_score: float = 0.0
    health_category: HealthScoreCategory = HealthScoreCategory.POOR
    
    class Settings:
        name = "projects"
        indexes = [
            "domain",
            [("user_id", 1), ("created_at", -1)],
        ]
    
    @before_event([Replace, Insert])
    def update_timestamp(self):
        self.updated_at = datetime.utcnow()


class CrawlAudit(Document):
    """
    Time-series document storing technical crawl results.
    One document per URL per crawl session.
    """
    project_id: Indexed(str)
    url: Indexed(str)
    domain: Indexed(str)
    
    # Crawl Metadata
    crawl_session_id: str
    status: CrawlStatus = CrawlStatus.PENDING
    crawled_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Response Data
    status_code: Optional[int] = None
    content_type: Optional[str] = None
    page_size_bytes: Optional[int] = None
    load_time_ms: Optional[float] = None
    
    # SEO Elements
    title: Optional[str] = None
    title_length: Optional[int] = None
    meta_description: Optional[str] = None
    meta_description_length: Optional[int] = None
    canonical_url: Optional[str] = None
    robots_meta: Optional[str] = None
    
    # Technical Analysis
    core_web_vitals: CoreWebVitals = Field(default_factory=CoreWebVitals)
    headings: HeadingHierarchy = Field(default_factory=HeadingHierarchy)
    schema_markup: List[SchemaMarkup] = []
    images_without_alt: List[ImageAltIssue] = []
    
    # Link Analysis
    internal_links: List[InternalLink] = []
    external_links: List[str] = []
    broken_links_count: int = 0
    
    # Issues
    issues: List[PageIssue] = []
    issue_counts: Dict[str, int] = Field(default_factory=dict)
    
    # Raw Content (optional, for NLP processing)
    word_count: Optional[int] = None
    readability_score: Optional[float] = None
    content_fingerprint: Optional[str] = None
    
    class Settings:
        name = "crawl_audits"
        timeseries = {
            "timeField": "crawled_at",
            "metaField": "project_id",
            "granularity": "minutes"
        }
        indexes = [
            "url",
            [("project_id", 1), ("crawled_at", -1)],
            [("domain", 1), ("crawl_session_id", 1)],
        ]


class LocalSearchRanking(Document):
    """
    Hyper-local map pack and organic rankings.
    Tracks rankings from multiple geo-coordinates.
    """
    project_id: Indexed(str)
    keyword: Indexed(str)
    location_name: str
    coordinates: Dict[str, float]  # lat, lng
    
    # Google Maps Results
    map_pack_rank: Optional[int] = None  # 1-3 for map pack
    map_pack_present: bool = False
    
    # Local Organic Results
    organic_rank: Optional[int] = None
    organic_url: Optional[str] = None
    
    # GMB Data (if applicable)
    gmb_rating: Optional[float] = None
    gmb_review_count: Optional[int] = None
    gmb_category: Optional[str] = None
    
    # Competitor GMBs in same area
    competitor_gmbs: List[Dict[str, Any]] = []
    
    # SERP Features
    local_ads_present: bool = False
    knowledge_panel_present: bool = False
    
    scanned_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "local_search_rankings"
        timeseries = {
            "timeField": "scanned_at",
            "metaField": "project_id",
            "granularity": "hours"
        }
        indexes = [
            [("project_id", 1), ("keyword", 1), ("scanned_at", -1)],
            [("coordinates.lat", 1), ("coordinates.lng", 1)],
        ]


class CompetitorSnapshot(Document):
    """
    Competitor SERP positioning and content tracking.
    """
    project_id: Indexed(str)
    competitor_domain: Indexed(str)
    keyword: Indexed(str)
    
    # Ranking Data
    position: int
    previous_position: Optional[int] = None
    position_change: int = 0
    
    # Content Analysis
    page_title: Optional[str] = None
    page_url: str
    content_length: Optional[int] = None
    estimated_traffic: Optional[int] = None
    
    # Change Detection
    content_changed: bool = False
    content_fingerprint: Optional[str] = None
    title_changed: bool = False
    last_seen: datetime
    
    captured_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "competitor_snapshots"
        timeseries = {
            "timeField": "captured_at",
            "metaField": "project_id",
            "granularity": "hours"
        }
        indexes = [
            [("project_id", 1), ("competitor_domain", 1), ("captured_at", -1)],
        ]


class ContentGapAnalysis(Document):
    """
    NLP-processed content gap data.
    """
    project_id: Indexed(str)
    target_keyword: Indexed(str)
    
    # LSI Keywords found in competitors but missing on target
    missing_lsi_keywords: List[Dict[str, Any]] = []  # {keyword, relevance_score, competitor_usage}
    
    # Semantic topics
    topic_clusters: List[Dict[str, Any]] = []
    
    # Entity analysis
    entities_present: List[str] = []
    entities_missing: List[str] = []
    
    # Content recommendations
    suggested_headings: List[str] = []
    suggested_word_count: Optional[int] = None
    readability_target: Optional[float] = None
    
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "content_gap_analyses"
        indexes = [
            [("project_id", 1), ("target_keyword", 1), ("analyzed_at", -1)],
        ]


class BacklinkProfile(Document):
    """
    Individual backlink records with toxicity scoring.
    """
    project_id: Indexed(str)
    referring_domain: Indexed(str)
    referring_page: str
    target_page: str
    
    # Link Attributes
    anchor_text: str
    link_type: str  # "dofollow" | "nofollow" | "ugc" | "sponsored"
    
    # Toxicity Analysis
    metrics: BacklinkMetrics = Field(default_factory=lambda: BacklinkMetrics(
        first_seen=datetime.utcnow(),
        last_checked=datetime.utcnow()
    ))
    
    # Flags
    is_suspicious: bool = False
    suspicion_reasons: List[str] = []
    disavow_recommended: bool = False
    disavowed: bool = False
    
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "backlink_profiles"
        indexes = [
            [("project_id", 1), ("referring_domain", 1)],
            [("project_id", 1), ("disavow_recommended", 1)],
            [("metrics.toxic_score", -1)],
        ]


class ServerLogEntry(Document):
    """
    Parsed server log entries for crawl budget analysis.
    """
    project_id: Indexed(str)
    timestamp: datetime
    
    # Request Data
    ip_address: Optional[str] = None
    user_agent: str
    is_googlebot: bool = False
    is_bingbot: bool = False
    bot_verified: bool = False  # DNS reverse lookup verified
    
    # URL Data
    request_url: str
    status_code: int
    response_size: int
    response_time_ms: float
    
    # Crawl Behavior
    crawl_depth: Optional[int] = None
    referer: Optional[str] = None
    
    class Settings:
        name = "server_logs"
        timeseries = {
            "timeField": "timestamp",
            "metaField": "project_id",
            "granularity": "seconds"
        }
        indexes = [
            [("project_id", 1), ("is_googlebot", 1), ("timestamp", -1)],
        ]


class ROIPrediction(Document):
    """
    Predictive ROI calculations for keyword opportunities.
    """
    project_id: Indexed(str)
    keyword: Indexed(str)
    
    # Input Metrics
    search_volume: int
    keyword_difficulty: float  # 0-100
    current_position: Optional[int] = None
    target_position: int = 3  # Goal: top 3
    
    # CTR Model (based on position)
    estimated_ctr_current: Optional[float] = None
    estimated_ctr_target: float
    
    # Conversion Metrics
    conversion_rate: float = 0.02  # Default 2%
    average_order_value: float = 100.0
    
    # Predictions
    predicted_monthly_clicks: int
    predicted_monthly_conversions: int
    predicted_monthly_revenue: float
    
    # Value
    estimated_monthly_value: float
    implementation_cost: float = 0.0
    roi_percentage: float
    payback_months: Optional[float] = None
    
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "roi_predictions"
        indexes = [
            [("project_id", 1), ("roi_percentage", -1)],
        ]


class LeadEvent(Document):
    """
    Lead tracking events from organic traffic.
    """
    project_id: Indexed(str)
    session_id: str
    
    # Attribution
    landing_page: str
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    
    # Event Details
    event_type: str  # "call_click", "directions_click", "form_submit", etc.
    element_selector: Optional[str] = None
    page_path: str
    
    # SEO Context
    organic_keyword: Optional[str] = None  # From Search Console integration
    search_console_position: Optional[int] = None
    
    # User Context (anonymized)
    device_type: str  # "desktop", "mobile", "tablet"
    geo_country: Optional[str] = None
    geo_city: Optional[str] = None
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "lead_events"
        timeseries = {
            "timeField": "timestamp",
            "metaField": "project_id",
            "granularity": "minutes"
        }
        indexes = [
            [("project_id", 1), ("event_type", 1), ("timestamp", -1)],
        ]


class AIActionCard(Document):
    """
    AI-generated actionable recommendations.
    """
    project_id: Indexed(str)
    card_id: str = Field(..., description="Unique card identifier")
    
    # Content
    title: str
    description: str
    category: str  # "technical", "content", "local", "competitor"
    severity: IssueSeverity
    
    # Impact Prediction
    estimated_impact: str  # "high", "medium", "low"
    estimated_effort: str  # "high", "medium", "low"
    potential_traffic_gain: Optional[int] = None
    
    # Context
    affected_urls: List[str] = []
    related_keywords: List[str] = []
    
    # User Interaction
    status: str = "pending"  # "pending", "swiped_left", "swiped_right", "completed", "dismissed"
    dismissed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    user_notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    class Settings:
        name = "ai_action_cards"
        indexes = [
            [("project_id", 1), ("status", 1), ("severity", 1)],
            [("card_id", 1)],
        ]
