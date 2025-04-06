"""
Main QA service implementation.

This module implements the IQAService interface to provide Q&A functionality
for the profile building process, following SOLID principles.
"""

from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime, timezone

from ...utils.logging import get_logger, log_execution_time
from ...utils.errors import ValidationError, ResourceNotFoundError, ServiceError
from ...core.interfaces import AIClientInterface
from .interfaces import IQAService
from .models import Question, Answer, Conversation, ConversationSummary
from .question_generator import IQuestionGenerator
from .answer_evaluator import IAnswerEvaluator
from .information_extractor import IInformationExtractor
from .conversation_memory import IConversationMemory

logger = get_logger(__name__)

class QAService(IQAService):
    """
    Main QA service implementation.
    
    This class follows the Dependency Inversion Principle by depending on
    abstractions (interfaces) rather than concrete implementations.
    """
    
    def __init__(
        self,
        question_generator: IQuestionGenerator,
        answer_evaluator: IAnswerEvaluator,
        information_extractor: IInformationExtractor,
        conversation_memory: IConversationMemory
    ):
        """
        Initialize the QA service with its dependencies.
        
        Args:
            question_generator: Component for generating questions
            answer_evaluator: Component for evaluating answers
            information_extractor: Component for extracting information
            conversation_memory: Component for storing conversations
        """
        self._question_generator = question_generator
        self._answer_evaluator = answer_evaluator
        self._information_extractor = information_extractor
        self._conversation_memory = conversation_memory
        self._initialized = False
        logger.info("Initialized QAService")
    
    async def initialize(self) -> None:
        """Initialize the service and its dependencies."""
        if not self._initialized:
            logger.info("Initializing QA service")
            
            # Initialize all dependencies
            await self._question_generator.initialize()
            await self._answer_evaluator.initialize()
            await self._information_extractor.initialize()
            await self._conversation_memory.initialize()
            
            self._initialized = True
            logger.info("QA service initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown the service and release resources."""
        if self._initialized:
            logger.info("Shutting down QA service")
            
            # Shutdown all dependencies
            await self._question_generator.shutdown()
            await self._answer_evaluator.shutdown()
            await self._information_extractor.shutdown()
            await self._conversation_memory.shutdown()
            
            self._initialized = False
            logger.info("QA service shut down successfully")
    
    @log_execution_time(logger)
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
            
        Raises:
            ValidationError: If the profile data is invalid
            ServiceError: If questions cannot be generated
        """
        if not self._initialized:
            await self.initialize()
        
        if not profile_data:
            logger.error("Empty profile data provided")
            raise ValidationError("Profile data cannot be empty")
        
        try:
            # Use the question generator to create questions
            questions = await self._question_generator.generate_questions(
                profile_data=profile_data,
                categories=categories
            )
            
            logger.info(f"Generated {len(questions)} questions")
            return questions
            
        except Exception as e:
            logger.exception(f"Error generating questions: {str(e)}")
            raise ServiceError(f"Failed to generate questions: {str(e)}")
    
    @log_execution_time(logger)
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
            
        Raises:
            ValidationError: If the inputs are invalid
            ServiceError: If the evaluation fails
        """
        if not self._initialized:
            await self.initialize()
        
        if not answer.response:
            logger.error("Empty answer response provided")
            raise ValidationError("Answer response cannot be empty")
        
        try:
            # Use the answer evaluator to evaluate the answer
            evaluated_answer = await self._answer_evaluator.evaluate_answer(
                question=question,
                answer=answer,
                profile_data=profile_data
            )
            
            # Extract information from the answer
            extracted_info = await self._information_extractor.extract_information(
                question=question,
                answer=evaluated_answer
            )
            
            # Update the answer with extracted information
            updated_answer = evaluated_answer.copy()
            updated_answer.extracted_info = extracted_info
            
            logger.info(f"Evaluated answer to question {question.question_id}")
            return updated_answer
            
        except Exception as e:
            logger.exception(f"Error evaluating answer: {str(e)}")
            raise ServiceError(f"Failed to evaluate answer: {str(e)}")
    
    @log_execution_time(logger)
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
            
        Raises:
            ValidationError: If the user ID is invalid
            ServiceError: If the conversation cannot be created
        """
        if not self._initialized:
            await self.initialize()
        
        if not user_id:
            logger.error("Empty user ID provided")
            raise ValidationError("User ID cannot be empty")
        
        try:
            # Use the conversation memory to create a conversation
            conversation = await self._conversation_memory.create_conversation(
                user_id=user_id,
                context=initial_context
            )
            
            logger.info(f"Created conversation {conversation.conversation_id} for user {user_id}")
            return conversation
            
        except Exception as e:
            logger.exception(f"Error creating conversation: {str(e)}")
            raise ServiceError(f"Failed to create conversation: {str(e)}")
    
    @log_execution_time(logger)
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
            
        Raises:
            ResourceNotFoundError: If the conversation does not exist
            ValidationError: If the message content is invalid
            ServiceError: If the message cannot be processed
        """
        if not self._initialized:
            await self.initialize()
        
        if not message_content:
            logger.error("Empty message content provided")
            raise ValidationError("Message content cannot be empty")
        
        try:
            # Get the conversation
            conversation = await self._conversation_memory.get_conversation(conversation_id)
            if not conversation:
                logger.error(f"Conversation {conversation_id} not found")
                raise ResourceNotFoundError(f"Conversation {conversation_id} not found")
            
            # Add the user message to the conversation
            await self._conversation_memory.add_message(
                conversation_id=conversation_id,
                role="user",
                content=message_content,
                metadata=message_metadata
            )
            
            # Determine if this is an answer to a question
            is_answer = False
            question = None
            question_id = None
            
            if message_metadata and "question_id" in message_metadata:
                question_id = message_metadata["question_id"]
                is_answer = True
            
            # Process the message differently based on whether it's an answer
            if is_answer and question_id:
                # This is an answer to a specific question
                # We would normally get the question from a repository
                # For now, we'll create a synthetic question
                question = Question(
                    question_id=question_id,
                    category=message_metadata.get("category", "general"),
                    question_text=message_metadata.get("question_text", ""),
                    expected_response_type="text",
                    required=False,
                    follow_up_questions=[]
                )
                
                # Create an answer object
                answer = Answer(
                    question_id=question_id,
                    response=message_content
                )
                
                # Evaluate the answer and extract information
                profile_data = conversation.context.get("profile_data", {})
                profile_data["user_id"] = conversation.user_id
                
                evaluated_answer = await self.evaluate_answer(
                    question=question,
                    answer=answer,
                    profile_data=profile_data
                )
                
                # Generate follow-up questions if needed
                follow_up_questions = []
                if evaluated_answer.needs_follow_up:
                    follow_up_questions = await self._question_generator.generate_follow_up_questions(
                        question=question,
                        answer=evaluated_answer,
                        profile_data=profile_data
                    )
                
                # Create the assistant's response
                if follow_up_questions:
                    response_content = f"Thank you for your answer. I'd like to ask a follow-up question: {follow_up_questions[0].question_text}"
                    response_metadata = {
                        "question_id": follow_up_questions[0].question_id,
                        "is_follow_up": True,
                        "parent_question_id": question_id
                    }
                else:
                    # Get the next question from a different category
                    next_questions = await self.generate_questions(
                        profile_data=profile_data,
                        categories=None
                    )
                    
                    if next_questions:
                        response_content = f"Thank you for sharing that information. Let's move on to another topic. {next_questions[0].question_text}"
                        response_metadata = {
                            "question_id": next_questions[0].question_id,
                            "category": next_questions[0].category
                        }
                    else:
                        response_content = "Thank you for providing all that information. I think we have a good understanding of your profile now."
                        response_metadata = {"conversation_complete": True}
                
                # Add the assistant's response to the conversation
                await self._conversation_memory.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response_content,
                    metadata=response_metadata
                )
                
                # Return the response data
                return {
                    "response": response_content,
                    "metadata": response_metadata,
                    "evaluated_answer": evaluated_answer.dict(),
                    "follow_up_questions": [q.dict() for q in follow_up_questions],
                    "extracted_info": evaluated_answer.extracted_info
                }
                
            else:
                # This is a general message, not an answer to a specific question
                # Generate a question based on the message content
                profile_data = conversation.context.get("profile_data", {})
                profile_data["user_id"] = conversation.user_id
                profile_data["latest_message"] = message_content
                
                new_questions = await self.generate_questions(
                    profile_data=profile_data,
                    categories=None
                )
                
                if new_questions:
                    response_content = f"Thank you for sharing that. {new_questions[0].question_text}"
                    response_metadata = {
                        "question_id": new_questions[0].question_id,
                        "category": new_questions[0].category
                    }
                else:
                    response_content = "Thank you for sharing that information. Is there anything specific about your profile that you'd like to discuss?"
                    response_metadata = {}
                
                # Add the assistant's response to the conversation
                await self._conversation_memory.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response_content,
                    metadata=response_metadata
                )
                
                # Extract information from the message
                extracted_info = await self._information_extractor.extract_information(
                    question=Question(
                        question_id="synthetic",
                        category="general",
                        question_text="Tell me about yourself",
                        expected_response_type="text",
                        required=False,
                        follow_up_questions=[]
                    ),
                    answer=Answer(
                        question_id="synthetic",
                        response=message_content
                    )
                )
                
                # Return the response data
                return {
                    "response": response_content,
                    "metadata": response_metadata,
                    "next_questions": [q.dict() for q in new_questions],
                    "extracted_info": extracted_info
                }
            
        except ResourceNotFoundError as e:
            # Re-raise resource not found errors
            raise e
        except ValidationError as e:
            # Re-raise validation errors
            raise e
        except Exception as e:
            logger.exception(f"Error processing message: {str(e)}")
            raise ServiceError(f"Failed to process message: {str(e)}")
    
    @log_execution_time(logger)
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
            
        Raises:
            ResourceNotFoundError: If the conversation does not exist
            ServiceError: If the summary cannot be generated
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Use the conversation memory to generate a summary
            summary = await self._conversation_memory.generate_summary(conversation_id)
            
            logger.info(f"Generated summary for conversation {conversation_id}")
            return summary
            
        except ResourceNotFoundError as e:
            # Re-raise resource not found errors
            raise e
        except Exception as e:
            logger.exception(f"Error generating conversation summary: {str(e)}")
            raise ServiceError(f"Failed to generate conversation summary: {str(e)}")


class QAServiceFactory:
    """
    Factory for creating QA service instances.
    
    This class applies the Factory pattern to create fully configured
    QA service instances with all required dependencies.
    """
    
    @staticmethod
    async def create_qa_service(
        ai_client: AIClientInterface,
        use_persistent_storage: bool = False,
        storage_path: Optional[str] = None
    ) -> QAService:
        """
        Create a fully configured QA service.
        
        Args:
            ai_client: AI client for model interactions
            use_persistent_storage: Whether to use persistent storage
            storage_path: Path for persistent storage (if used)
            
        Returns:
            Fully configured QAService instance
        """
        # Create the information extractor
        information_extractor = AIInformationExtractor(ai_client=ai_client)
        
        # Create the question generator
        question_generator = AIQuestionGenerator(ai_client=ai_client)
        
        # Create the answer evaluator
        answer_evaluator = AIAnswerEvaluator(ai_client=ai_client)
        
        # Create the conversation memory
        if use_persistent_storage:
            from .conversation_memory import PersistentConversationMemory
            conversation_memory = PersistentConversationMemory(
                ai_client=ai_client,
                information_extractor=information_extractor,
                storage_path=storage_path or "./data/conversations"
            )
        else:
            from .conversation_memory import InMemoryConversationMemory
            conversation_memory = InMemoryConversationMemory(
                information_extractor=information_extractor
            )
        
        # Create the QA service
        service = QAService(
            question_generator=question_generator,
            answer_evaluator=answer_evaluator,
            information_extractor=information_extractor,
            conversation_memory=conversation_memory
        )
        
        # Initialize the service
        await service.initialize()
        
        return service 