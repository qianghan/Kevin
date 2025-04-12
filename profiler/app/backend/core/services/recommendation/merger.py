import logging
from typing import Dict, Any, List

class RecommendationMerger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def merge_recommendations(
        self,
        standard_recommendations: List[Dict[str, Any]],
        university_recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Merge standard and university recommendations with error handling"""
        try:
            merged = []

            # Add standard recommendations first
            for rec in standard_recommendations:
                rec["source"] = "standard"
                merged.append(rec)

            # Add university recommendations if available
            if university_recommendations:
                for rec in university_recommendations:
                    rec["source"] = "university"
                    merged.append(rec)
            else:
                self.logger.info("No university recommendations available, using standard recommendations only")

            # Sort recommendations by relevance score if available
            merged.sort(
                key=lambda x: float(x.get("relevance_score", 0)),
                reverse=True
            )

            # Add recommendation type metadata
            for rec in merged:
                rec["is_university"] = rec["source"] == "university"
                rec["recommendation_type"] = "university" if rec["source"] == "university" else "standard"

            return merged

        except Exception as e:
            self.logger.error(f"Error merging recommendations: {e}")
            # Return standard recommendations as fallback
            return [{"source": "standard", "is_university": False, "recommendation_type": "standard", **rec}
                   for rec in standard_recommendations] 