from typing import List, Dict, Any
import logging

class UniversityMapper:
    """Maps university data from Kevin API to internal format"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def map_universities(self, search_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Map search results to university recommendations"""
        universities = []
        
        try:
            # Extract documents from search results
            documents = search_results.get("documents", [])
            
            for doc in documents:
                universities.append({
                    "id": doc.get("id"),
                    "name": doc.get("metadata", {}).get("name", "Unknown University"),
                    "location": doc.get("metadata", {}).get("location", "Unknown Location"),
                    "programs": doc.get("metadata", {}).get("programs", []),
                    "admission_rate": doc.get("metadata", {}).get("admission_rate"),
                    "match_score": int(doc.get("score", 0) * 100) if "score" in doc else None,
                    "match_reason": self._generate_match_reason(doc)
                })
        except Exception as e:
            self.logger.error(f"Error mapping universities: {e}")
            
        return universities
    
    async def map_university_details(self, university_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map university details to internal format"""
        try:
            return {
                "id": university_data.get("id"),
                "name": university_data.get("metadata", {}).get("name", "Unknown University"),
                "location": university_data.get("metadata", {}).get("location", "Unknown Location"),
                "description": university_data.get("metadata", {}).get("description", ""),
                "programs": university_data.get("metadata", {}).get("programs", []),
                "admission_rate": university_data.get("metadata", {}).get("admission_rate"),
                "student_body_size": university_data.get("metadata", {}).get("student_body_size"),
                "tuition": university_data.get("metadata", {}).get("tuition"),
                "website": university_data.get("metadata", {}).get("website")
            }
        except Exception as e:
            self.logger.error(f"Error mapping university details: {e}")
            return {}
    
    def _generate_match_reason(self, document: Dict[str, Any]) -> str:
        """Generate a reason why this university matches the profile"""
        metadata = document.get("metadata", {})
        reasons = []
        
        if "programs" in metadata and metadata["programs"]:
            reasons.append(f"Offers programs matching your interests")
            
        if "admission_rate" in metadata and metadata["admission_rate"]:
            reasons.append(f"Has an admission rate of {metadata['admission_rate']}%")
            
        if not reasons:
            return "Matches your profile"
            
        return "; ".join(reasons)
