"""
Service interfaces for the Profiler application.

This module defines abstract base classes for all services in the application
to provide a consistent interface and enable dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel

# Document Service interfaces
class DocumentAnalysisResult(BaseModel):
    """Results of a document analysis."""
    document_id: str
    text_content: str
    metadata: Dict[str, Any]
    sections: List[Dict[str, Any]]
    analysis: Dict[str, Any]
    extracted_data: Dict[str, Any]

class IDocumentService(ABC):
    """Interface for document analysis services."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the service and release resources."""
        pass
    
    @abstractmethod
    async def analyze_document(self, document_content: str, document_type: str, 
                              user_id: str, metadata: Optional[Dict[str, Any]] = None) -> DocumentAnalysisResult:
        """
        Analyze a document and extract structured data.
        
        Args:
            document_content: The content of the document
            document_type: The type of document (e.g., resume, cover_letter)
            user_id: The ID of the user who owns the document
            metadata: Additional metadata about the document
            
        Returns:
            DocumentAnalysisResult with analysis and extracted data
            
        Raises:
            ValidationError: If the document type is invalid
            ServiceError: If the document cannot be analyzed
        """
        pass
    
    @abstractmethod
    async def validate_document_type(self, document_type: str) -> bool:
        """
        Validate that a document type is supported.
        
        Args:
            document_type: The type of document to validate
            
        Returns:
            True if the document type is valid, False otherwise
        """
        pass

# Recommendation Service interfaces
class Recommendation(BaseModel):
    """A recommendation for improving a profile."""
    category: str
    title: str
    description: str
    priority: int
    action_items: List[str]
    confidence: float

class ProfileSummary(BaseModel):
    """A summary of a user's profile."""
    strengths: List[str]
    areas_for_improvement: List[str]
    unique_selling_points: List[str]
    overall_quality: float
    last_updated: str

class IRecommendationService(ABC):
    """Interface for recommendation generation services."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the service and release resources."""
        pass
    
    @abstractmethod
    async def generate_recommendations(self, profile_data: Dict[str, Any], 
                                     categories: Optional[List[str]] = None) -> List[Recommendation]:
        """
        Generate recommendations based on profile data.
        
        Args:
            profile_data: The user's profile data
            categories: Optional list of categories to generate recommendations for
            
        Returns:
            List of Recommendation objects
            
        Raises:
            ValidationError: If the profile data is invalid
            ServiceError: If recommendations cannot be generated
        """
        pass
    
    @abstractmethod
    async def get_profile_summary(self, profile_data: Dict[str, Any]) -> ProfileSummary:
        """
        Generate a summary of the user's profile.
        
        Args:
            profile_data: The user's profile data
            
        Returns:
            ProfileSummary object
            
        Raises:
            ValidationError: If the profile data is invalid
            ServiceError: If the summary cannot be generated
        """
        pass

# QA Service interfaces
class Question(BaseModel):
    """A question about a profile."""
    question_id: str
    category: str
    question: str
    expected_response_type: str
    required: bool

class Answer(BaseModel):
    """An answer to a question."""
    question_id: str
    response: Any
    confidence: float
    quality_score: Optional[float] = None

class IQuestionGenerator(ABC):
    """Interface for question generation."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the question generator."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the question generator and release resources."""
        pass
    
    @abstractmethod
    async def generate_questions(
        self, 
        profile_data: Dict[str, Any],
        categories: Optional[List[str]] = None,
        count: int = 3
    ) -> List[Any]:
        """
        Generate questions based on profile data.
        
        Args:
            profile_data: The user's profile data
            categories: Optional list of categories to generate questions for
            count: Number of questions to generate
            
        Returns:
            List of Question objects
            
        Raises:
            ValidationError: If the profile data is invalid
            ServiceError: If questions cannot be generated
        """
        pass
    
    @abstractmethod
    async def generate_follow_up_questions(
        self,
        question: Any,
        answer: Any,
        profile_data: Dict[str, Any]
    ) -> List[Any]:
        """
        Generate follow-up questions based on a previous question and answer.
        
        Args:
            question: The original question
            answer: The answer to the original question
            profile_data: The user's profile data
            
        Returns:
            List of follow-up Question objects
            
        Raises:
            ValidationError: If the inputs are invalid
            ServiceError: If follow-up questions cannot be generated
        """
        pass

class IQAService(ABC):
    """Interface for QA generation and evaluation services."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the service and release resources."""
        pass
    
    @abstractmethod
    async def generate_questions(self, profile_data: Dict[str, Any], 
                               categories: Optional[List[str]] = None) -> List[Question]:
        """
        Generate questions based on profile data.
        
        Args:
            profile_data: The user's profile data
            categories: Optional list of categories to generate questions for
            
        Returns:
            List of Question objects
            
        Raises:
            ValidationError: If the profile data is invalid
            ServiceError: If questions cannot be generated
        """
        pass
    
    @abstractmethod
    async def evaluate_answer(self, question: Question, answer: Answer, 
                            profile_data: Dict[str, Any]) -> Answer:
        """
        Evaluate an answer to a question.
        
        Args:
            question: The question being answered
            answer: The answer to evaluate
            profile_data: The user's profile data
            
        Returns:
            Updated Answer object with quality score
            
        Raises:
            ValidationError: If the answer is invalid
            ServiceError: If the answer cannot be evaluated
        """
        pass

# Profile Service interfaces
class ProfileState(BaseModel):
    """The current state of a profile build session."""
    profile_id: str
    user_id: str
    current_section: str
    sections_completed: List[str]
    sections_remaining: List[str]
    profile_data: Dict[str, Any]
    last_updated: str
    status: str

class IProfileService(ABC):
    """Interface for profile management services."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service and its components."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the service and release resources."""
        pass
    
    @abstractmethod
    async def create_profile(self, user_id: str, initial_data: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a new profile for a user.
        
        Args:
            user_id: The ID of the user
            initial_data: Optional initial data for the profile
            
        Returns:
            Profile state object
            
        Raises:
            ValidationError: If the user ID is invalid
            ServiceError: If the profile cannot be created
        """
        pass
    
    @abstractmethod
    async def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> Any:
        """
        Update an existing profile.
        
        Args:
            profile_id: The ID of the profile to update
            updates: The updates to apply to the profile
            
        Returns:
            Updated profile state object
            
        Raises:
            ResourceNotFoundError: If the profile does not exist
            ValidationError: If the updates are invalid
            ServiceError: If the profile cannot be updated
        """
        pass
    
    @abstractmethod
    async def get_profile(self, profile_id: str) -> Any:
        """
        Get a profile by ID.
        
        Args:
            profile_id: The ID of the profile to get
            
        Returns:
            Profile state object
            
        Raises:
            ResourceNotFoundError: If the profile does not exist
            ServiceError: If the profile cannot be retrieved
        """
        pass
    
    @abstractmethod
    async def delete_profile(self, profile_id: str) -> None:
        """
        Delete a profile by ID.
        
        Args:
            profile_id: The ID of the profile to delete
            
        Raises:
            ResourceNotFoundError: If the profile does not exist
            ServiceError: If the profile cannot be deleted
        """
        pass 