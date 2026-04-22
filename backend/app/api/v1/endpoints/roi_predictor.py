"""
API Endpoints for Predictive ROI Engine.
Calculates potential traffic and conversion gains.
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.database import ROIPrediction, Project

router = APIRouter()


# ============== CTR MODEL ==============
# Industry average CTR by position (based on Ahrefs/Backlinko data)
CTR_BY_POSITION = {
    1: 0.279,   # Position 1: 27.9%
    2: 0.153,   # Position 2: 15.3%
    3: 0.111,   # Position 3: 11.1%
    4: 0.082,   # Position 4: 8.2%
    5: 0.061,   # Position 5: 6.1%
    6: 0.046,   # Position 6: 4.6%
    7: 0.035,   # Position 7: 3.5%
    8: 0.028,   # Position 8: 2.8%
    9: 0.022,   # Position 9: 2.2%
    10: 0.018,  # Position 10: 1.8%
}

DEFAULT_CTR = 0.015  # Position 11+


def get_ctr_by_position(position: int) -> float:
    """Get expected CTR for a given position."""
    if position <= 0:
        return 0
    return CTR_BY_POSITION.get(position, DEFAULT_CTR)


# ============== REQUEST/RESPONSE MODELS ==============
class ROICalculationRequest(BaseModel):
    project_id: str
    keyword: str
    search_volume: int = Field(..., gt=0)
    keyword_difficulty: float = Field(..., ge=0, le=100)
    current_position: Optional[int] = None
    target_position: int = Field(default=3, ge=1, le=10)
    conversion_rate: float = Field(default=0.02, ge=0, le=1)
    average_order_value: float = Field(default=100.0, gt=0)
    implementation_cost: float = Field(default=0.0, ge=0)


class ROIResponse(BaseModel):
    id: str
    keyword: str
    search_volume: int
    keyword_difficulty: float
    current_position: Optional[int]
    target_position: int
    estimated_ctr_current: Optional[float]
    estimated_ctr_target: float
    predicted_monthly_clicks: int
    predicted_monthly_conversions: int
    predicted_monthly_revenue: float
    estimated_monthly_value: float
    roi_percentage: float
    payback_months: Optional[float]
    calculated_at: str


# ============== ENDPOINTS ==============
@router.post("/calculate", response_model=ROIResponse)
async def calculate_roi(request: ROICalculationRequest):
    """
    Calculate predictive ROI for keyword ranking improvement.
    
    Models traffic gains from current to target position,
    applies conversion rates, and calculates revenue impact.
    """
    # Verify project exists
    project = await Project.get(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get CTR values
    current_ctr = get_ctr_by_position(request.current_position) if request.current_position else 0
    target_ctr = get_ctr_by_position(request.target_position)
    
    # Calculate metrics
    monthly_clicks_current = int(request.search_volume * current_ctr)
    monthly_clicks_target = int(request.search_volume * target_ctr)
    
    # Use target clicks for prediction
    predicted_clicks = monthly_clicks_target
    predicted_conversions = int(predicted_clicks * request.conversion_rate)
    predicted_revenue = predicted_conversions * request.average_order_value
    
    # Calculate ROI
    if request.implementation_cost > 0:
        monthly_profit = predicted_revenue * 0.3  # Assume 30% profit margin
        roi_percentage = ((monthly_profit * 12) / request.implementation_cost - 1) * 100
        payback_months = request.implementation_cost / monthly_profit if monthly_profit > 0 else None
    else:
        roi_percentage = 999.9  # Infinite ROI if no cost
        payback_months = 0.0
    
    # Create and save prediction
    prediction = ROIPrediction(
        project_id=request.project_id,
        keyword=request.keyword,
        search_volume=request.search_volume,
        keyword_difficulty=request.keyword_difficulty,
        current_position=request.current_position,
        target_position=request.target_position,
        estimated_ctr_current=current_ctr,
        estimated_ctr_target=target_ctr,
        predicted_monthly_clicks=predicted_clicks,
        predicted_monthly_conversions=predicted_conversions,
        predicted_monthly_revenue=predicted_revenue,
        estimated_monthly_value=predicted_revenue,
        implementation_cost=request.implementation_cost,
        roi_percentage=roi_percentage,
        payback_months=payback_months
    )
    
    await prediction.insert()
    
    return _prediction_to_response(prediction)


@router.get("/predictions/{project_id}", response_model=List[ROIResponse])
async def get_project_predictions(
    project_id: str,
    min_roi: Optional[float] = None,
    limit: int = Query(default=50, le=200)
):
    """
    Get all ROI predictions for a project.
    
    Optionally filter by minimum ROI percentage.
    """
    query = ROIPrediction.find(ROIPrediction.project_id == project_id)
    
    if min_roi is not None:
        query = query.find(ROIPrediction.roi_percentage >= min_roi)
    
    predictions = await query.sort(-ROIPrediction.roi_percentage).limit(limit).to_list()
    
    return [_prediction_to_response(p) for p in predictions]


@router.get("/top-opportunities/{project_id}")
async def get_top_opportunities(
    project_id: str,
    limit: int = Query(default=10, le=50)
):
    """
    Get highest ROI keyword opportunities.
    
    Considers both ROI percentage and absolute traffic potential.
    """
    predictions = await ROIPrediction.find(
        ROIPrediction.project_id == project_id
    ).sort(-ROIPrediction.estimated_monthly_value).limit(limit * 2).to_list()
    
    # Score by combination of ROI and value
    scored = []
    for p in predictions:
        # Normalize scores (0-100)
        roi_score = min(p.roi_percentage, 500) / 5  # Cap at 500% for scoring
        value_score = min(p.estimated_monthly_value / 1000, 100)
        
        combined_score = roi_score * 0.4 + value_score * 0.6
        scored.append((combined_score, p))
    
    # Sort by combined score
    scored.sort(key=lambda x: x[0], reverse=True)
    
    return {
        "opportunities": [
            {
                "keyword": p.keyword,
                "roi_percentage": round(p.roi_percentage, 1),
                "monthly_value": round(p.estimated_monthly_value, 2),
                "keyword_difficulty": p.keyword_difficulty,
                "target_position": p.target_position,
                "score": round(score, 1)
            }
            for score, p in scored[:limit]
        ]
    }


@router.get("/portfolio-summary/{project_id}")
async def get_portfolio_summary(project_id: str):
    """
    Get aggregate ROI metrics across all keyword predictions.
    """
    pipeline = [
        {"$match": {"project_id": project_id}},
        {
            "$group": {
                "_id": None,
                "total_keywords": {"$sum": 1},
                "avg_roi": {"$avg": "$roi_percentage"},
                "total_monthly_value": {"$sum": "$estimated_monthly_value"},
                "avg_difficulty": {"$avg": "$keyword_difficulty"},
                "total_monthly_clicks": {"$sum": "$predicted_monthly_clicks"}
            }
        }
    ]
    
    collection = ROIPrediction.get_motor_collection()
    result = await collection.aggregate(pipeline).to_list(length=1)
    
    if not result:
        return {
            "message": "No predictions found for this project"
        }
    
    stats = result[0]
    
    return {
        "total_keywords_analyzed": stats["total_keywords"],
        "average_roi_percentage": round(stats["avg_roi"], 1),
        "total_predicted_monthly_value": round(stats["total_monthly_value"], 2),
        "total_predicted_monthly_clicks": stats["total_monthly_clicks"],
        "average_keyword_difficulty": round(stats["avg_difficulty"], 1),
        "annual_projected_value": round(stats["total_monthly_value"] * 12, 2)
    }


# ============== HELPER FUNCTIONS ==============
def _prediction_to_response(prediction: ROIPrediction) -> ROIResponse:
    """Convert ROIPrediction to response model."""
    return ROIResponse(
        id=str(prediction.id),
        keyword=prediction.keyword,
        search_volume=prediction.search_volume,
        keyword_difficulty=prediction.keyword_difficulty,
        current_position=prediction.current_position,
        target_position=prediction.target_position,
        estimated_ctr_current=prediction.estimated_ctr_current,
        estimated_ctr_target=prediction.estimated_ctr_target,
        predicted_monthly_clicks=prediction.predicted_monthly_clicks,
        predicted_monthly_conversions=prediction.predicted_monthly_conversions,
        predicted_monthly_revenue=prediction.predicted_monthly_revenue,
        estimated_monthly_value=prediction.estimated_monthly_value,
        roi_percentage=prediction.roi_percentage,
        payback_months=prediction.payback_months,
        calculated_at=prediction.calculated_at.isoformat()
    )
