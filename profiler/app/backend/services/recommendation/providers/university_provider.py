from abc import ABC, abstractmethod
from typing import List, Dict, Any

class UniversityProvider(ABC):
    """Interface for retrieving university recommendations"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider"""
        pass
        
    @abstractmethod
    async def get_universities(self, profile_data: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Get university recommendations based on profile data"""
        pass
        
    @abstractmethod
    async def get_university_details(self, university_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific university"""
        pass
        
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the provider and release resources"""
        pass
