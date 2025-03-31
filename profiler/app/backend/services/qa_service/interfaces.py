"""
Interfaces for the QA service components.

This module defines abstract base classes for various components of the QA service
following the Interface Segregation and Dependency Inversion principles.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from .models import Question, Answer, Conversation, ConversationSummary

class IQuestionGenerator(ABC):
    """Interface for generating questions based on profile data."""
    
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
    ) -> List[Question]:
        """
        Generate questions based on profile data.
        
        Args:
            profile_data: The user's profile data
            categories: Optional list of categories to generate questions for
            count: Number of questions to generate
            
        Returns:
            List of Question objects
        """
        pass
    
    @abstractmethod
    async def generate_follow_up_questions(
        self,
        question: Question,
        answer: Answer,
        profile_data: Dict[str, Any]
    ) -> List[Question]:
        """
        Generate follow-up questions based on a previous question and answer.
        
        Args:
            question: The original question
            answer: The answer to the original question
            profile_data: The user's profile data
            
        Returns:
            List of follow-up Question objects
        """
        pass

class IAnswerEvaluator(ABC):
    """Interface for evaluating answers to questions."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the answer evaluator."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the answer evaluator and release resources."""
        pass
    
    @abstractmethod
    async def evaluate_answer(
        self, 
        question: Question, 
        answer: Answer,
        profile_data: Dict[str, Any]
    ) -> Answer:
        """
        Evaluate an answer to a question.
        
        Args:
            question: The question being answered
            answer: The answer to evaluate
            profile_data: The user's profile data
            
        Returns:
            Updated Answer object with quality score
        """
        pass
    
    @abstractmethod
    async def check_answer_completion(
        self,
        question: Question,
        answer: Answer
    ) -> bool:
        """
        Check if an answer is complete or needs follow-up.
        
        Args:
            question: The question being answered
            answer: The answer to check
            
        Returns:
            True if the answer is complete, False if follow-up is needed
        """
        pass

class IInformationExtractor(ABC):
    """Interface for extracting structured information from answers."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the information extractor."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the information extractor and release resources."""
        pass
    
    @abstractmethod
    async def extract_information(
        self,
        question: Question,
        answer: Answer
    ) -> Dict[str, Any]:
        """
        Extract structured information from an answer.
        
        Args:
            question: The question that was answered
            answer: The answer to extract information from
            
        Returns:
            Structured information extracted from the answer
        """
        pass
    
    @abstractmethod
    async def extract_conversation_information(
        self,
        conversation: Conversation
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract structured information from an entire conversation.
        
        Args:
            conversation: The conversation to extract information from
            
        Returns:
            Structured information extracted from the conversation,
            organized by category
        """
        pass

class IFollowUpGenerator(ABC):
    """Interface for generating follow-up questions and prompts."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the follow-up generator."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the follow-up generator and release resources."""
        pass
    
    @abstractmethod
    async def generate_follow_up(
        self,
        question: Question,
        answer: Answer,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Generate follow-up questions based on a question and answer.
        
        Args:
            question: The original question
            answer: The answer to the original question
            context: Optional additional context
            
        Returns:
            List of follow-up questions as strings
        """
        pass

class IConversationMemory(ABC):
    """Interface for managing conversation state and history."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the conversation memory."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the conversation memory and release resources."""
        pass
    
    @abstractmethod
    async def create_conversation(
        self,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            user_id: The user's ID
            context: Optional initial context for the conversation
            
        Returns:
            A new Conversation object
        """
        pass
    
    @abstractmethod
    async def get_conversation(
        self,
        conversation_id: str
    ) -> Optional[Conversation]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: The conversation's ID
            
        Returns:
            The Conversation object or None if not found
        """
        pass
    
    @abstractmethod
    async def update_conversation(
        self,
        conversation: Conversation
    ) -> Conversation:
        """
        Update a conversation with new information.
        
        Args:
            conversation: The updated conversation
            
        Returns:
            The updated Conversation object
        """
        pass
    
    @abstractmethod
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: The conversation's ID
            role: The role of the message sender
            content: The message content
            metadata: Optional message metadata
            
        Returns:
            The updated Conversation object
        """
        pass
    
    @abstractmethod
    async def generate_summary(
        self,
        conversation_id: str
    ) -> ConversationSummary:
        """
        Generate a summary of a conversation.
        
        Args:
            conversation_id: The conversation's ID
            
        Returns:
            A ConversationSummary object
        """
        pass
    
    @abstractmethod
    async def clear_conversation(
        self,
        conversation_id: str
    ) -> None:
        """
        Clear a conversation's messages.
        
        Args:
            conversation_id: The conversation's ID
        """
        pass

class IQAService(ABC):
    """Interface for the QA service."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the service and release resources."""
        pass
    
    @abstractmethod
    async def generate_questions(
        self, 
        profile_data: Dict[str, Any],
        categories: Optional[List[str]] = None
    ) -> List[Question]:
        """
        Generate questions based on profile data.
        
        Args:
            profile_data: The user's profile data
            categories: Optional list of categories to generate questions for
            
        Returns:
            List of Question objects
        """
        pass
    
    @abstractmethod
    async def evaluate_answer(
        self, 
        question: Question, 
        answer: Answer,
        profile_data: Dict[str, Any]
    ) -> Answer:
        """
        Evaluate an answer to a question.
        
        Args:
            question: The question being answered
            answer: The answer to evaluate
            profile_data: The user's profile data
            
        Returns:
            Updated Answer object with quality score
        """
        pass
    
    @abstractmethod
    async def create_conversation(
        self,
        user_id: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        Create a new conversation with a user.
        
        Args:
            user_id: The user's ID
            initial_context: Optional initial context for the conversation
            
        Returns:
            A new Conversation object
        """
        pass
    
    @abstractmethod
    async def process_message(
        self,
        conversation_id: str,
        message_content: str,
        message_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message in a conversation.
        
        Args:
            conversation_id: The conversation's ID
            message_content: The content of the user's message
            message_metadata: Optional metadata for the message
            
        Returns:
            Response data including assistant message, extracted information,
            and follow-up questions
        """
        pass
    
    @abstractmethod
    async def get_conversation_summary(
        self,
        conversation_id: str
    ) -> ConversationSummary:
        """
        Get a summary of a conversation.
        
        Args:
            conversation_id: The conversation's ID
            
        Returns:
            A ConversationSummary object
        """
        pass 