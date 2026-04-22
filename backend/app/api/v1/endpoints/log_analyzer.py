"""
API Endpoints for Server Log Analysis.
Parses logs to monitor Googlebot crawl budget and behavior.
"""
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel

from app.models.database import ServerLogEntry, Project

router = APIRouter()


# ============== REQUEST/RESPONSE MODELS ==============
class LogUploadResponse(BaseModel):
    message: str
    entries_parsed: int
    googlebot_hits: int
    errors: int


class CrawlStats(BaseModel):
    total_requests: int
    googlebot_requests: int
    unique_pages_crawled: int
    avg_response_time: float
    error_rate: float
    crawl_budget_efficiency: str


# ============== ENDPOINTS ==============
@router.post("/upload/{project_id}", response_model=LogUploadResponse)
async def upload_server_logs(
    project_id: str,
    file: UploadFile = File(...)
):
    """
    Upload and parse server log files (Apache/Nginx format).
    """
    project = await Project.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    content = await file.read()
    lines = content.decode('utf-8').split('\n')
    
    entries_parsed = 0
    googlebot_hits = 0
    errors = 0
    
    for line in lines:
        if not line.strip():
            continue
        
        try:
            entry = _parse_log_line(line, project_id)
            if entry:
                await entry.insert()
                entries_parsed += 1
                if entry.is_googlebot:
                    googlebot_hits += 1
        except Exception:
            errors += 1
    
    return LogUploadResponse(
        message="Log file processed successfully",
        entries_parsed=entries_parsed,
        googlebot_hits=googlebot_hits,
        errors=errors
    )


@router.get("/stats/{project_id}", response_model=CrawlStats)
async def get_crawl_stats(
    project_id: str,
    days: int = Query(default=7, le=30)
):
    """
    Get aggregated crawl statistics.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    pipeline = [
        {
            "$match": {
                "project_id": project_id,
                "timestamp": {"$gte": cutoff}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_requests": {"$sum": 1},
                "googlebot_requests": {
                    "$sum": {"$cond": ["$is_googlebot", 1, 0]}
                },
                "unique_pages": {"$addToSet": "$request_url"},
                "avg_response": {"$avg": "$response_time_ms"},
                "errors": {
                    "$sum": {
                        "$cond": [{"$gte": ["$status_code", 400]}, 1, 0]
                    }
                }
            }
        }
    ]
    
    collection = ServerLogEntry.get_motor_collection()
    result = await collection.aggregate(pipeline).to_list(length=1)
    
    if not result:
        return CrawlStats(
            total_requests=0,
            googlebot_requests=0,
            unique_pages_crawled=0,
            avg_response_time=0.0,
            error_rate=0.0,
            crawl_budget_efficiency="N/A"
        )
    
    stats = result[0]
    total = stats["total_requests"]
    errors = stats.get("errors", 0)
    
    # Calculate efficiency
    if stats["googlebot_requests"] > 0:
        error_rate = (errors / stats["googlebot_requests"]) * 100
        if error_rate < 5:
            efficiency = "Excellent"
        elif error_rate < 15:
            efficiency = "Good"
        elif error_rate < 30:
            efficiency = "Needs Work"
        else:
            efficiency = "Poor"
    else:
        error_rate = 0.0
        efficiency = "No Data"
    
    return CrawlStats(
        total_requests=total,
        googlebot_requests=stats["googlebot_requests"],
        unique_pages_crawled=len(stats.get("unique_pages", [])),
        avg_response_time=round(stats["avg_response"], 2) if stats.get("avg_response") else 0.0,
        error_rate=round(error_rate, 1),
        crawl_budget_efficiency=efficiency
    )


@router.get("/top-crawled/{project_id}")
async def get_most_crawled_pages(
    project_id: str,
    days: int = Query(default=7, le=30),
    limit: int = Query(default=20, le=100)
):
    """
    Get pages with most Googlebot crawl activity.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    pipeline = [
        {
            "$match": {
                "project_id": project_id,
                "is_googlebot": True,
                "timestamp": {"$gte": cutoff}
            }
        },
        {
            "$group": {
                "_id": "$request_url",
                "crawl_count": {"$sum": 1},
                "avg_response": {"$avg": "$response_time_ms"},
                "error_count": {
                    "$sum": {"$cond": [{"$gte": ["$status_code", 400]}, 1, 0]}
                }
            }
        },
        {"$sort": {"crawl_count": -1}},
        {"$limit": limit}
    ]
    
    collection = ServerLogEntry.get_motor_collection()
    results = await collection.aggregate(pipeline).to_list(length=None)
    
    return {
        "pages": [
            {
                "url": r["_id"],
                "crawl_count": r["crawl_count"],
                "avg_response_ms": round(r["avg_response"], 2),
                "error_count": r["error_count"]
            }
            for r in results
        ]
    }


def _parse_log_line(line: str, project_id: str) -> Optional[ServerLogEntry]:
    """
    Parse Apache/Nginx combined log format.
    Example: 127.0.0.1 - - [10/Oct/2023:13:55:36 -0700] "GET / HTTP/1.1" 200 1234
    """
    import re
    
    # Common log format regex
    pattern = r'^(\S+) \S+ \S+ \[([\w:/]+\s[+\-]\d{4})\] "(\S+) (\S+) (\S+)" (\d{3}) (\d+) "([^"]+)" "([^"]+)"'
    match = re.match(pattern, line)
    
    if not match:
        return None
    
    ip, timestamp_str, method, url, protocol, status, size, referer, user_agent = match.groups()
    
    # Parse timestamp
    try:
        timestamp = datetime.strptime(timestamp_str, "%d/%b/%Y:%H:%M:%S %z")
    except ValueError:
        timestamp = datetime.utcnow()
    
    # Check for Googlebot
    is_googlebot = "Googlebot" in user_agent
    
    # Basic bot verification (simplified)
    bot_verified = is_googlebot and ip.startswith("66.")  # Simplified check
    
    return ServerLogEntry(
        project_id=project_id,
        ip_address=ip,
        timestamp=timestamp,
        request_url=url,
        status_code=int(status),
        response_size=int(size),
        response_time_ms=0.0,  # Would need additional parsing
        user_agent=user_agent,
        is_googlebot=is_googlebot,
        is_bingbot="bingbot" in user_agent.lower(),
        bot_verified=bot_verified,
        referer=referer
    )
