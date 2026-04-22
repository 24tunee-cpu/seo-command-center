"""
SERP and Local Search API integrations.
Supports SerpApi, Google Places API, and direct scraping fallback.
"""
import os
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

import httpx
from serpapi import GoogleSearch

from app.core.config import get_settings
from app.models.database import LocalSearchRanking

settings = get_settings()


class LocalRadarService:
    """
    Hyper-local Maps Radar for tracking map pack and organic rankings
    across multiple geographic coordinates.
    """
    
    def __init__(self):
        self.serpapi_key = settings.serpapi_key
        self.places_api_key = settings.google_places_api_key
    
    async def scan_local_rankings(
        self,
        project_id: str,
        domain: str,
        keyword: str,
        locations: List[Dict[str, Any]]
    ) -> List[LocalSearchRanking]:
        """
        Scan local rankings for a keyword across multiple coordinates.
        
        Args:
            locations: List of {name, lat, lng, radius_m}
        """
        results = []
        
        for location in locations:
            ranking = await self._fetch_local_serp(
                project_id=project_id,
                domain=domain,
                keyword=keyword,
                location_name=location["name"],
                lat=location["lat"],
                lng=location["lng"],
                radius_m=location.get("radius_m", 5000)
            )
            results.append(ranking)
        
        return results
    
    async def _fetch_local_serp(
        self,
        project_id: str,
        domain: str,
        keyword: str,
        location_name: str,
        lat: float,
        lng: float,
        radius_m: int
    ) -> LocalSearchRanking:
        """
        Fetch local SERP using SerpApi with GPS coordinates.
        """
        if not self.serpapi_key:
            # Return empty result if no API key
            return LocalSearchRanking(
                project_id=project_id,
                keyword=keyword,
                location_name=location_name,
                coordinates={"lat": lat, "lng": lng},
                search_radius=radius_m
            )
        
        params = {
            "engine": "google_maps",
            "q": keyword,
            "ll": f"@{lat},{lng},{14}z",  # GPS coordinates with zoom
            "radius": radius_m,
            "api_key": self.serpapi_key,
            "hl": "en",
            "gl": "us"
        }
        
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            return self._parse_maps_results(
                results, project_id, keyword, location_name, lat, lng, radius_m, domain
            )
        except Exception as e:
            # Return error result
            return LocalSearchRanking(
                project_id=project_id,
                keyword=keyword,
                location_name=location_name,
                coordinates={"lat": lat, "lng": lng},
                search_radius=radius_m,
                map_pack_present=False
            )
    
    def _parse_maps_results(
        self,
        data: Dict[str, Any],
        project_id: str,
        keyword: str,
        location_name: str,
        lat: float,
        lng: float,
        radius_m: int,
        target_domain: str
    ) -> LocalSearchRanking:
        """
        Parse SerpApi Google Maps results.
        """
        ranking = LocalSearchRanking(
            project_id=project_id,
            keyword=keyword,
            location_name=location_name,
            coordinates={"lat": lat, "lng": lng},
            search_radius=radius_m,
            map_pack_present=False
        )
        
        local_results = data.get("local_results", [])
        
        if not local_results:
            return ranking
        
        ranking.map_pack_present = True
        competitor_gmbs = []
        
        # Find target domain in local results (map pack)
        for idx, result in enumerate(local_results[:10], 1):
            result_url = result.get("website", "")
            result_domain = urlparse(result_url).netloc.replace("www.", "")
            target_clean = target_domain.replace("www.", "")
            
            # Check if this is the target domain
            if result_domain == target_clean or target_clean in result_domain:
                ranking.map_pack_rank = idx
                ranking.gmb_rating = result.get("rating")
                ranking.gmb_review_count = result.get("reviews")
                ranking.gmb_category = result.get("type")
            else:
                # Store competitor data
                competitor_gmbs.append({
                    "position": idx,
                    "business_name": result.get("title"),
                    "domain": result_domain,
                    "rating": result.get("rating"),
                    "review_count": result.get("reviews"),
                    "category": result.get("type")
                })
        
        ranking.competitor_gmbs = competitor_gmbs
        
        return ranking
    
    async def scan_organic_local(
        self,
        project_id: str,
        domain: str,
        keyword: str,
        location: Dict[str, Any]
    ) -> LocalSearchRanking:
        """
        Scan organic SERP for local results (not just map pack).
        """
        if not self.serpapi_key:
            return LocalSearchRanking(
                project_id=project_id,
                keyword=keyword,
                location_name=location["name"],
                coordinates={"lat": location["lat"], "lng": location["lng"]}
            )
        
        params = {
            "engine": "google",
            "q": keyword,
            "location": location["name"],
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
            "api_key": self.serpapi_key,
            "device": "desktop"
        }
        
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            return self._parse_organic_results(
                results, project_id, keyword, location, domain
            )
        except Exception:
            return LocalSearchRanking(
                project_id=project_id,
                keyword=keyword,
                location_name=location["name"],
                coordinates={"lat": location["lat"], "lng": location["lng"]}
            )
    
    def _parse_organic_results(
        self,
        data: Dict[str, Any],
        project_id: str,
        keyword: str,
        location: Dict[str, Any],
        target_domain: str
    ) -> LocalSearchRanking:
        """
        Parse organic SERP results for local pack and organic listings.
        """
        ranking = LocalSearchRanking(
            project_id=project_id,
            keyword=keyword,
            location_name=location["name"],
            coordinates={"lat": location["lat"], "lng": location["lng"]},
            search_radius=location.get("radius_m", 5000)
        )
        
        organic_results = data.get("organic_results", [])
        local_pack = data.get("local_pack", {})
        
        # Check local pack
        if local_pack:
            ranking.map_pack_present = True
            places = local_pack.get("places", [])
            for idx, place in enumerate(places, 1):
                place_domain = self._extract_domain(place.get("website", ""))
                if place_domain == target_domain.replace("www.", ""):
                    ranking.map_pack_rank = idx
                    ranking.gmb_rating = place.get("rating")
                    ranking.gmb_review_count = place.get("reviews")
        
        # Check organic results
        target_clean = target_domain.replace("www.", "")
        for idx, result in enumerate(organic_results, 1):
            result_domain = self._extract_domain(result.get("link", ""))
            if result_domain == target_clean:
                ranking.organic_rank = idx
                ranking.organic_url = result.get("link")
                break
        
        # Check for SERP features
        ranking.knowledge_panel_present = "knowledge_graph" in data
        ranking.local_ads_present = bool(data.get("ads", []))
        
        return ranking
    
    def _extract_domain(self, url: str) -> str:
        """Extract clean domain from URL."""
        if not url:
            return ""
        domain = urlparse(url).netloc
        return domain.replace("www.", "")
    
    async def get_places_details(
        self,
        place_id: str
    ) -> Dict[str, Any]:
        """
        Fetch detailed GMB information using Google Places API.
        """
        if not self.places_api_key:
            return {}
        
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "name,rating,reviews,formatted_address,website,formatted_phone_number",
            "key": self.places_api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            return response.json().get("result", {})
    
    def generate_geo_grid(
        self,
        center_lat: float,
        center_lng: float,
        radius_km: float = 5,
        grid_size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate a grid of coordinates around a center point for local ranking tracking.
        
        Args:
            center_lat: Center latitude
            center_lng: Center longitude  
            radius_km: Radius in kilometers
            grid_size: Grid dimensions (5x5 default)
        
        Returns:
            List of location dicts with lat/lng
        """
        import math
        
        locations = []
        
        # Convert radius to degrees (approximate)
        # 1 degree latitude ≈ 111 km
        lat_step = (radius_km * 2) / (grid_size - 1) / 111
        lng_step = (radius_km * 2) / (grid_size - 1) / (111 * math.cos(math.radians(center_lat)))
        
        start_lat = center_lat - ((grid_size - 1) / 2) * lat_step
        start_lng = center_lng - ((grid_size - 1) / 2) * lng_step
        
        for i in range(grid_size):
            for j in range(grid_size):
                lat = start_lat + i * lat_step
                lng = start_lng + j * lng_step
                
                # Calculate distance from center
                dist_km = math.sqrt(
                    ((lat - center_lat) * 111) ** 2 + 
                    ((lng - center_lng) * 111 * math.cos(math.radians(center_lat))) ** 2
                )
                
                locations.append({
                    "name": f"Grid-{i}-{j}",
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                    "distance_km": round(dist_km, 2),
                    "radius_m": 2000
                })
        
        return locations
