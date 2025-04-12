from typing import Dict, Any, List
import logging

class RecommendationMerger:
    """Merges various types of recommendations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def merge_recommendations(self, standard_recs: Dict[str, Any], 
                                   university_recs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge standard recommendations with university recommendations"""
        try:
            merged = standard_recs.copy()
            
            # Add universities section if it doesn't exist
            if "universities" not in merged:
                merged["universities"] = []
                
            # Replace with new university recommendations
            merged["universities"] = university_recs
            
            # Track the addition in the sources section
            if "sources" not in merged:
                merged["sources"] = []
                
            if university_recs and "kevin" not in [s.get("name") for s in merged.get("sources", [])]:
                merged["sources"].append({
                    "name": "kevin",
                    "type": "university_database", 
                    "count": len(university_recs)
                })
                
            return merged
        except Exception as e:
            self.logger.error(f"Error merging recommendations: {e}")
            return standard_recs
