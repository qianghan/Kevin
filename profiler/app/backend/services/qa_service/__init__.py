"""
QA Service package for handling question answering and interactive profile building.

This package implements SOLID principles for a modular, extendable QA system.
"""

from .service import QAService
from .models import Question, Answer, QuestionCategory, Conversation, ConversationSummary
from .interfaces import (
    IQAService, 
    IQuestionGenerator, 
    IAnswerEvaluator, 
    IInformationExtractor,
    IFollowUpGenerator,
    IConversationMemory
)

# Factory for creating QA services
class QAServiceFactory:
    """Factory for creating QA service instances with different configurations."""
    
    @staticmethod
    async def create_qa_service(
        ai_client,
        use_persistent_storage=False,
        storage_path="./data/conversations"
    ):
        """
        Create a QA service with the specified configuration.
        
        Args:
            ai_client: AI client for generating responses
            use_persistent_storage: Whether to use persistent storage for conversations
            storage_path: Path to store conversations if using persistent storage
            
        Returns:
            Initialized QA service
        """
        from .question_generator import AIQuestionGenerator
        from .answer_evaluator import AIAnswerEvaluator
        from .information_extractor import AIInformationExtractor
        from .conversation_memory import InMemoryConversationMemory, FileSystemConversationMemory
        
        # Create components
        question_generator = AIQuestionGenerator(ai_client=ai_client)
        answer_evaluator = AIAnswerEvaluator(ai_client=ai_client)
        information_extractor = AIInformationExtractor(ai_client=ai_client)
        
        # Create memory based on configuration
        if use_persistent_storage:
            conversation_memory = FileSystemConversationMemory(
                storage_path=storage_path,
                information_extractor=information_extractor
            )
        else:
            conversation_memory = InMemoryConversationMemory(
                information_extractor=information_extractor
            )
        
        # Create and initialize service
        service = QAService(
            ai_client=ai_client,
            question_generator=question_generator,
            answer_evaluator=answer_evaluator,
            information_extractor=information_extractor,
            conversation_memory=conversation_memory
        )
        
        await service.initialize()
        return service

__all__ = [
    'QAService',
    'QAServiceFactory',
    'Question',
    'Answer',
    'QuestionCategory',
    'Conversation',
    'ConversationSummary',
    'IQAService',
    'IQuestionGenerator',
    'IAnswerEvaluator',
    'IInformationExtractor',
    'IFollowUpGenerator',
    'IConversationMemory'
] 