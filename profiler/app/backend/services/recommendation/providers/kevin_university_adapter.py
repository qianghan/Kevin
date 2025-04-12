import httpx
from typing import List, Dict, Any, Optional
import logging
from .university_provider import UniversityProvider
from ..mappers.university_mapper import UniversityMapper

class KevinUniversityAdapter(UniversityProvider):
    """Adapter for Kevin's University API Service"""
    
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.base_url = config.get("external_services.kevin.base_url", "http://localhost:5000")
        self.api_key = config.get("external_services.kevin.api_key", "")
        self.timeout = config.get("external_services.kevin.timeout_seconds", 5)
        self.client = None
        self.university_mapper = UniversityMapper()
        self.initialized = False
        
    async def initialize(self):
        """Initialize the adapter with HTTP client"""
        if not self.initialized:
            self.logger.info("Initializing Kevin University Adapter")
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout
            )
            self.initialized = True
            self.logger.info("Kevin University Adapter initialized successfully")
        
    async def get_universities(self, profile_data: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Get university recommendations using Kevin's API"""
        if not self.initialized:
            await self.initialize()
            
        try:
            # Extract relevant criteria from profile data
            search_criteria = self._extract_search_criteria(profile_data)
            query = self._build_query(profile_data)
            
            # Call Kevin's search/documents API
            self.logger.debug(f"Querying Kevin API with query: {query}")
            response = await self.client.post(
                "/api/search/documents",
                json={
                    "query": query,
                    "filter": search_criteria.get("filters", {}),
                    "limit": limit
                }
            )
            response.raise_for_status()
            
            # Map the response to our internal format
            search_results = response.json()
            return await self.university_mapper.map_universities(search_results)
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error from Kevin API: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            self.logger.error(f"Request error to Kevin API: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error getting universities: {str(e)}")
            return []
    
    async def get_university_details(self, university_id: str) -> Dict[str, Any]:
        """Get detailed information about a university"""
        if not self.initialized:
            await self.initialize()
            
        try:
            response = await self.client.get(f"/api/search/documents/{university_id}")
            response.raise_for_status()
            return await self.university_mapper.map_university_details(response.json())
        except Exception as e:
            self.logger.error(f"Error getting university details: {str(e)}")
            return {}
    
    def _extract_search_criteria(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract search criteria from profile data"""
        criteria = {
            "filters": {}
        }
        
        # Add academic filters
        academic_data = profile_data.get("sections", {}).get("academic", {}).get("data", {})
        if "gpa" in academic_data:
            criteria["filters"]["min_gpa"] = max(0, academic_data["gpa"] - 0.5)
        
        # Add location preferences if available
        preferences = profile_data.get("context", {}).get("university_preferences", {})
        if "locations" in preferences:
            criteria["filters"]["locations"] = preferences["locations"]
            
        return criteria
    
    def _build_query(self, profile_data: Dict[str, Any]) -> str:
        """Build a search query from profile data"""
        # Extract interests and goals
        interests = []
        goals = ""
        
        personal_data = profile_data.get("sections", {}).get("personal", {}).get("data", {})
        if "interests" in personal_data:
            interests = personal_data["interests"]
        if "career_goals" in personal_data:
            goals = personal_data["career_goals"]
            
        # Build query string
        query_parts = []
        if interests:
            query_parts.append(f"programs in {', '.join(interests)}")
        if goals:
            query_parts.append(f"career path for {goals}")
            
        if not query_parts:
            return "university recommendations"
            
        return " ".join(query_parts)
    
    async def shutdown(self):
        """Close the HTTP client"""
        if self.client:
            self.logger.info("Shutting down Kevin University Adapter")
            await self.client.aclose()
            self.initialized = False
            self.logger.info("Kevin University Adapter shut down successfully")
