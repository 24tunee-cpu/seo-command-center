"""
API Endpoints for Hyper-Local Maps Radar.
Tracks local pack and organic rankings across geographic grids.
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from app.models.database import LocalSearchRanking, Project
from app.services.serp_service import LocalRadarService

router = APIRouter()
radar_service = LocalRadarService()


# ============== REQUEST/RESPONSE MODELS ==============
class LocationPoint(BaseModel):
    name: str
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    radius_m: int = Field(default=2000, ge=500, le=50000)


class LocalScanRequest(BaseModel):
    project_id: str
    keyword: str
    locations: List[LocationPoint]


class GeoGridRequest(BaseModel):
    project_id: str
    keyword: str
    center_lat: float
    center_lng: float
    radius_km: float = Field(default=5, le=20)
    grid_size: int = Field(default=5, ge=3, le=9)


class LocalRankingResponse(BaseModel):
    id: str
    keyword: str
    location_name: str
    coordinates: dict
    map_pack_rank: Optional[int]
    map_pack_present: bool
    organic_rank: Optional[int]
    gmb_rating: Optional[float]
    gmb_review_count: Optional[int]
    distance_km: Optional[float]
    scanned_at: str


class RankingHeatmapPoint(BaseModel):
    lat: float
    lng: float
    rank: Optional[int]
    grid_position: str
    intensity: float  # For heatmap visualization


# ============== ENDPOINTS ==============
@router.post("/scan", response_model=List[LocalRankingResponse])
async def scan_local_rankings(request: LocalScanRequest):
    """
    Scan local rankings for a keyword across multiple geographic points.
    
    Returns map pack rankings, organic rankings, and GMB data for each location.
    """
    # Verify project exists
    project = await Project.get(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Convert locations to dict format
    locations = [loc.dict() for loc in request.locations]
    
    # Perform scans
    results = await radar_service.scan_local_rankings(
        project_id=request.project_id,
        domain=project.domain,
        keyword=request.keyword,
        locations=locations
    )
    
    # Save results to database
    for ranking in results:
        await ranking.insert()
    
    return [_ranking_to_response(r) for r in results]


@router.post("/geo-grid-scan", response_model=List[LocalRankingResponse])
async def scan_geo_grid(request: GeoGridRequest):
    """
    Generate a geographic grid around a center point and scan all positions.
    
    Creates a grid (e.g., 5x5 = 25 points) radiating from the center,
    then scans local rankings at each point for comprehensive coverage.
    """
    # Verify project exists
    project = await Project.get(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Generate grid points
    grid_locations = radar_service.generate_geo_grid(
        center_lat=request.center_lat,
        center_lng=request.center_lng,
        radius_km=request.radius_km,
        grid_size=request.grid_size
    )
    
    # Scan all grid points
    results = await radar_service.scan_local_rankings(
        project_id=request.project_id,
        domain=project.domain,
        keyword=request.keyword,
        locations=grid_locations
    )
    
    # Save results
    for ranking in results:
        await ranking.insert()
    
    return [_ranking_to_response(r) for r in results]


@router.get("/rankings/{project_id}", response_model=List[LocalRankingResponse])
async def get_project_rankings(
    project_id: str,
    keyword: Optional[str] = None,
    days: int = Query(default=30, le=90),
    limit: int = Query(default=100, le=500)
):
    """
    Retrieve historical local ranking data for a project.
    
    Optionally filter by keyword and time range.
    """
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = LocalSearchRanking.find(
        LocalSearchRanking.project_id == project_id,
        LocalSearchRanking.scanned_at >= cutoff_date
    )
    
    if keyword:
        query = query.find(LocalSearchRanking.keyword == keyword)
    
    rankings = await query.sort(-LocalSearchRanking.scanned_at).limit(limit).to_list()
    
    return [_ranking_to_response(r) for r in rankings]


@router.get("/heatmap-data/{project_id}")
async def get_local_heatmap_data(
    project_id: str,
    keyword: str,
    days: int = Query(default=7, le=30)
):
    """
    Get formatted heatmap data for visualization.
    
    Returns coordinates with ranking intensity for heatmap plotting.
    Green = Rank 1-3 (high intensity), Red = Rank 10+ (low intensity).
    """
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get latest scan for each location
    pipeline = [
        {
            "$match": {
                "project_id": project_id,
                "keyword": keyword,
                "scanned_at": {"$gte": cutoff_date}
            }
        },
        {
            "$sort": {"scanned_at": -1}
        },
        {
            "$group": {
                "_id": {
                    "lat": "$coordinates.lat",
                    "lng": "$coordinates.lng"
                },
                "rank": {"$first": "$map_pack_rank"},
                "organic_rank": {"$first": "$organic_rank"},
                "location_name": {"$first": "$location_name"}
            }
        }
    ]
    
    collection = LocalSearchRanking.get_motor_collection()
    results = await collection.aggregate(pipeline).to_list(length=None)
    
    heatmap_points = []
    for doc in results:
        rank = doc.get("rank") or doc.get("organic_rank") or 20
        
        # Calculate intensity (inverse of rank, normalized)
        if rank and rank <= 3:
            intensity = 1.0
        elif rank and rank <= 5:
            intensity = 0.7
        elif rank and rank <= 10:
            intensity = 0.4
        else:
            intensity = 0.1
        
        heatmap_points.append({
            "lat": doc["_id"]["lat"],
            "lng": doc["_id"]["lng"],
            "rank": rank,
            "location_name": doc.get("location_name"),
            "intensity": intensity
        })
    
    # Calculate summary statistics
    rankings = [p["rank"] for p in heatmap_points if p["rank"]]
    avg_rank = sum(rankings) / len(rankings) if rankings else None
    
    top3_count = sum(1 for r in rankings if r <= 3)
    top10_count = sum(1 for r in rankings if r <= 10)
    
    return {
        "keyword": keyword,
        "total_points": len(heatmap_points),
        "average_rank": round(avg_rank, 1) if avg_rank else None,
        "top_3_count": top3_count,
        "top_10_count": top10_count,
        "heatmap_data": heatmap_points
    }


@router.get("/ranking-trends/{project_id}")
async def get_ranking_trends(
    project_id: str,
    keyword: str,
    location_name: Optional[str] = None,
    days: int = Query(default=30, le=90)
):
    """
    Get time-series ranking trend data for charts.
    
    Returns daily average rankings for trend visualization.
    """
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = {
        "project_id": project_id,
        "keyword": keyword,
        "scanned_at": {"$gte": cutoff_date}
    }
    
    if location_name:
        query["location_name"] = location_name
    
    # Aggregate by day
    pipeline = [
        {"$match": query},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$scanned_at"
                    }
                },
                "avg_map_rank": {"$avg": "$map_pack_rank"},
                "avg_organic_rank": {"$avg": "$organic_rank"},
                "scan_count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    collection = LocalSearchRanking.get_motor_collection()
    results = await collection.aggregate(pipeline).to_list(length=None)
    
    return {
        "keyword": keyword,
        "days": days,
        "trend_data": [
            {
                "date": r["_id"],
                "avg_map_rank": round(r["avg_map_rank"], 1) if r["avg_map_rank"] else None,
                "avg_organic_rank": round(r["avg_organic_rank"], 1) if r["avg_organic_rank"] else None,
                "scan_count": r["scan_count"]
            }
            for r in results
        ]
    }


@router.get("/competitor-map/{project_id}")
async def get_competitor_map_data(
    project_id: str,
    keyword: str,
    days: int = Query(default=7, le=30)
):
    """
    Get competitor GMB data from local scans.
    
    Aggregates which competitors appear most frequently in the map pack.
    """
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get recent scans with competitor data
    rankings = await LocalSearchRanking.find(
        LocalSearchRanking.project_id == project_id,
        LocalSearchRanking.keyword == keyword,
        LocalSearchRanking.scanned_at >= cutoff_date,
        LocalSearchRanking.competitor_gmbs.exists & (LocalSearchRanking.competitor_gmbs != [])
    ).to_list()
    
    # Aggregate competitor appearances
    competitor_stats = {}
    for ranking in rankings:
        for comp in ranking.competitor_gmbs:
            name = comp.get("business_name", "Unknown")
            if name not in competitor_stats:
                competitor_stats[name] = {
                    "name": name,
                    "appearances": 0,
                    "avg_position": [],
                    "avg_rating": [],
                    "categories": set()
                }
            
            competitor_stats[name]["appearances"] += 1
            competitor_stats[name]["avg_position"].append(comp.get("position", 0))
            if comp.get("rating"):
                competitor_stats[name]["avg_rating"].append(comp["rating"])
            if comp.get("category"):
                competitor_stats[name]["categories"].add(comp["category"])
    
    # Format results
    results = []
    for comp in competitor_stats.values():
        positions = comp["avg_position"]
        ratings = comp["avg_rating"]
        
        results.append({
            "name": comp["name"],
            "appearances": comp["appearances"],
            "avg_position": round(sum(positions) / len(positions), 1) if positions else None,
            "avg_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
            "categories": list(comp["categories"])
        })
    
    # Sort by appearances (most frequent first)
    results.sort(key=lambda x: x["appearances"], reverse=True)
    
    return {
        "keyword": keyword,
        "days_analyzed": days,
        "competitors": results[:10]  # Top 10
    }


# ============== HELPER FUNCTIONS ==============
def _ranking_to_response(ranking: LocalSearchRanking) -> LocalRankingResponse:
    """Convert LocalSearchRanking to response model."""
    return LocalRankingResponse(
        id=str(ranking.id),
        keyword=ranking.keyword,
        location_name=ranking.location_name,
        coordinates=ranking.coordinates,
        map_pack_rank=ranking.map_pack_rank,
        map_pack_present=ranking.map_pack_present,
        organic_rank=ranking.organic_rank,
        gmb_rating=ranking.gmb_rating,
        gmb_review_count=ranking.gmb_review_count,
        distance_km=ranking.distance_km,
        scanned_at=ranking.scanned_at.isoformat()
    )
