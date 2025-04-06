"""
Conversation memory implementation.

This module implements the IConversationMemory interface to manage
conversation state and history for the QA service.
"""

from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime, timezone
import json
import asyncio

from ...utils.logging import get_logger, log_execution_time
from ...utils.errors import ValidationError, ResourceNotFoundError, ServiceError
from ...core.interfaces import AIClientInterface
from .interfaces import IConversationMemory, IInformationExtractor
from .models import Conversation, ConversationMessage, ConversationSummary, QuestionCategory
from .templates import CONVERSATION_SUMMARY_PROMPT

logger = get_logger(__name__)

class InMemoryConversationMemory(IConversationMemory):
    """
    In-memory implementation of conversation memory.
    
    This class manages conversations using in-memory storage.
    It follows the Single Responsibility Principle by focusing solely on
    conversation storage and retrieval.
    """
    
    def __init__(self, information_extractor: Optional[IInformationExtractor] = None):
        """
        Initialize the conversation memory.
        
        Args:
            information_extractor: Optional extractor for generating summaries
        """
        self._conversations: Dict[str, Conversation] = {}
        self._extractor = information_extractor
        self._initialized = False
        logger.info("Initialized InMemoryConversationMemory")
    
    async def initialize(self) -> None:
        """Initialize the conversation memory."""
        if not self._initialized:
            logger.info("Initializing conversation memory")
            self._initialized = True
    
    async def shutdown(self) -> None:
        """Shutdown the conversation memory and release resources."""
        if self._initialized:
            logger.info("Shutting down conversation memory")
            self._conversations.clear()
            self._initialized = False
    
    @log_execution_time(logger)
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
            
        Raises:
            ValidationError: If the user ID is invalid
        """
        if not self._initialized:
            await self.initialize()
        
        if not user_id:
            logger.error("Empty user ID provided")
            raise ValidationError("User ID cannot be empty")
        
        # Generate a unique conversation ID
        conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
        
        # Create timestamp
        now = datetime.now(timezone.utc)
        
        # Create new conversation
        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            context=context or {},
            start_time=now,
            last_updated=now
        )
        
        # Store conversation
        self._conversations[conversation_id] = conversation
        
        logger.info(f"Created conversation {conversation_id} for user {user_id}")
        return conversation
    
    @log_execution_time(logger)
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
        if not self._initialized:
            await self.initialize()
        
        conversation = self._conversations.get(conversation_id)
        
        if conversation:
            logger.info(f"Retrieved conversation {conversation_id}")
        else:
            logger.warning(f"Conversation {conversation_id} not found")
        
        return conversation
    
    @log_execution_time(logger)
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
            
        Raises:
            ResourceNotFoundError: If the conversation does not exist
        """
        if not self._initialized:
            await self.initialize()
        
        if conversation.conversation_id not in self._conversations:
            logger.error(f"Conversation {conversation.conversation_id} not found")
            raise ResourceNotFoundError(f"Conversation {conversation.conversation_id} not found")
        
        # Update last_updated timestamp
        conversation.last_updated = datetime.now(timezone.utc)
        
        # Store updated conversation
        self._conversations[conversation.conversation_id] = conversation
        
        logger.info(f"Updated conversation {conversation.conversation_id}")
        return conversation
    
    @log_execution_time(logger)
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
            
        Raises:
            ResourceNotFoundError: If the conversation does not exist
            ValidationError: If the role or content is invalid
        """
        if not self._initialized:
            await self.initialize()
        
        # Validate role
        valid_roles = ["user", "assistant", "system"]
        if role not in valid_roles:
            logger.error(f"Invalid role: {role}")
            raise ValidationError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        
        # Get conversation
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            logger.error(f"Conversation {conversation_id} not found")
            raise ResourceNotFoundError(f"Conversation {conversation_id} not found")
        
        # Create message
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add message to conversation
        conversation.messages.append(message)
        
        # Track questions and answers
        if metadata:
            if "question_id" in metadata:
                conversation.questions_asked.append(metadata["question_id"])
            elif "answer_id" in metadata and len(conversation.questions_asked) > len(conversation.answers_received):
                conversation.answers_received.append(metadata["answer_id"])
        
        # Update last_updated timestamp
        conversation.last_updated = datetime.now(timezone.utc)
        
        # Store updated conversation
        self._conversations[conversation_id] = conversation
        
        logger.info(f"Added {role} message to conversation {conversation_id}")
        return conversation
    
    @log_execution_time(logger)
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
            
        Raises:
            ResourceNotFoundError: If the conversation does not exist
            ServiceError: If the summary cannot be generated
        """
        if not self._initialized:
            await self.initialize()
        
        # Get conversation
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            logger.error(f"Conversation {conversation_id} not found")
            raise ResourceNotFoundError(f"Conversation {conversation_id} not found")
        
        logger.info(f"Generating summary for conversation {conversation_id}")
        
        # Extract categories covered
        categories_covered = set()
        for message in conversation.messages:
            if message.metadata and "category" in message.metadata:
                categories_covered.add(message.metadata["category"])
        
        # Use the information extractor if available
        extracted_info = {}
        if self._extractor:
            try:
                extracted_info = await self._extractor.extract_conversation_information(conversation)
            except Exception as e:
                logger.error(f"Error extracting information: {str(e)}")
                # Continue with empty extracted info
        
        # Calculate completion percentage
        completion_percentage = 0.0
        if conversation.questions_asked:
            # Simple metric: answers / questions ratio
            completion_percentage = min(100.0, (len(conversation.answers_received) / len(conversation.questions_asked)) * 100)
        
        # Create simple summary text
        summary_text = f"Conversation with {len(conversation.messages)} messages, covering {len(categories_covered)} categories."
        
        # Create summary
        summary = ConversationSummary(
            conversation_id=conversation_id,
            user_id=conversation.user_id,
            message_count=len(conversation.messages),
            categories_covered=list(categories_covered),
            extracted_info=extracted_info,
            completion_percentage=completion_percentage,
            summary_text=summary_text,
            generated_at=datetime.now(timezone.utc)
        )
        
        logger.info(f"Generated summary for conversation {conversation_id}")
        return summary
    
    @log_execution_time(logger)
    async def clear_conversation(
        self,
        conversation_id: str
    ) -> None:
        """
        Clear a conversation's messages.
        
        Args:
            conversation_id: The conversation's ID
            
        Raises:
            ResourceNotFoundError: If the conversation does not exist
        """
        if not self._initialized:
            await self.initialize()
        
        # Get conversation
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            logger.error(f"Conversation {conversation_id} not found")
            raise ResourceNotFoundError(f"Conversation {conversation_id} not found")
        
        # Clear messages
        conversation.messages = []
        conversation.questions_asked = []
        conversation.answers_received = []
        
        # Update last_updated timestamp
        conversation.last_updated = datetime.now(timezone.utc)
        
        # Store updated conversation
        self._conversations[conversation_id] = conversation
        
        logger.info(f"Cleared messages from conversation {conversation_id}")

class PersistentConversationMemory(IConversationMemory):
    """
    Persistent implementation of conversation memory.
    
    This class demonstrates the Open-Closed Principle by providing an
    alternative implementation that persists conversations to storage.
    """
    
    def __init__(
        self, 
        ai_client: AIClientInterface,
        information_extractor: Optional[IInformationExtractor] = None,
        storage_path: str = "./data/conversations"
    ):
        """
        Initialize the persistent conversation memory.
        
        Args:
            ai_client: AI client for generating summaries
            information_extractor: Optional extractor for generating summaries
            storage_path: Path to store conversations
        """
        self._client = ai_client
        self._extractor = information_extractor
        self._storage_path = storage_path
        self._cache: Dict[str, Conversation] = {}
        self._initialized = False
        logger.info(f"Initialized PersistentConversationMemory with storage at {storage_path}")
    
    async def initialize(self) -> None:
        """Initialize the conversation memory."""
        if not self._initialized:
            logger.info("Initializing persistent conversation memory")
            # Create storage directory if it doesn't exist
            # In a real implementation, this would be handled by a proper storage layer
            # (e.g., a database or file system abstraction)
            import os
            os.makedirs(self._storage_path, exist_ok=True)
            self._initialized = True
    
    async def shutdown(self) -> None:
        """Shutdown the conversation memory and release resources."""
        if self._initialized:
            logger.info("Shutting down persistent conversation memory")
            await self._flush_cache()
            self._cache.clear()
            self._initialized = False
    
    async def _flush_cache(self) -> None:
        """Flush the cache to persistent storage."""
        # In a real implementation, this would write to a database or file system
        # For this example, we'll just log it
        logger.info(f"Flushing conversation cache ({len(self._cache)} conversations)")
    
    async def _load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Load a conversation from persistent storage.
        
        Args:
            conversation_id: The conversation's ID
            
        Returns:
            The Conversation object or None if not found
        """
        # In a real implementation, this would read from a database or file system
        # For this example, we'll just check the cache
        return self._cache.get(conversation_id)
    
    async def _save_conversation(self, conversation: Conversation) -> None:
        """
        Save a conversation to persistent storage.
        
        Args:
            conversation: The conversation to save
        """
        # In a real implementation, this would write to a database or file system
        # For this example, we'll just update the cache
        self._cache[conversation.conversation_id] = conversation
    
    @log_execution_time(logger)
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
            
        Raises:
            ValidationError: If the user ID is invalid
        """
        if not self._initialized:
            await self.initialize()
        
        if not user_id:
            logger.error("Empty user ID provided")
            raise ValidationError("User ID cannot be empty")
        
        # Generate a unique conversation ID
        conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
        
        # Create timestamp
        now = datetime.now(timezone.utc)
        
        # Create new conversation
        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            context=context or {},
            start_time=now,
            last_updated=now
        )
        
        # Save conversation
        await self._save_conversation(conversation)
        
        logger.info(f"Created conversation {conversation_id} for user {user_id}")
        return conversation
    
    @log_execution_time(logger)
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
        if not self._initialized:
            await self.initialize()
        
        # Try to get from cache first
        conversation = self._cache.get(conversation_id)
        
        # If not in cache, try to load from storage
        if not conversation:
            conversation = await self._load_conversation(conversation_id)
        
        if conversation:
            logger.info(f"Retrieved conversation {conversation_id}")
        else:
            logger.warning(f"Conversation {conversation_id} not found")
        
        return conversation
    
    @log_execution_time(logger)
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
            
        Raises:
            ResourceNotFoundError: If the conversation does not exist
        """
        if not self._initialized:
            await self.initialize()
        
        # Check if conversation exists
        existing = await self.get_conversation(conversation.conversation_id)
        if not existing:
            logger.error(f"Conversation {conversation.conversation_id} not found")
            raise ResourceNotFoundError(f"Conversation {conversation.conversation_id} not found")
        
        # Update last_updated timestamp
        conversation.last_updated = datetime.now(timezone.utc)
        
        # Save updated conversation
        await self._save_conversation(conversation)
        
        logger.info(f"Updated conversation {conversation.conversation_id}")
        return conversation
    
    @log_execution_time(logger)
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
            
        Raises:
            ResourceNotFoundError: If the conversation does not exist
            ValidationError: If the role or content is invalid
        """
        if not self._initialized:
            await self.initialize()
        
        # Validate role
        valid_roles = ["user", "assistant", "system"]
        if role not in valid_roles:
            logger.error(f"Invalid role: {role}")
            raise ValidationError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        
        # Get conversation
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            logger.error(f"Conversation {conversation_id} not found")
            raise ResourceNotFoundError(f"Conversation {conversation_id} not found")
        
        # Create message
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add message to conversation
        conversation.messages.append(message)
        
        # Track questions and answers
        if metadata:
            if "question_id" in metadata:
                conversation.questions_asked.append(metadata["question_id"])
            elif "answer_id" in metadata and len(conversation.questions_asked) > len(conversation.answers_received):
                conversation.answers_received.append(metadata["answer_id"])
        
        # Update last_updated timestamp
        conversation.last_updated = datetime.now(timezone.utc)
        
        # Save updated conversation
        await self._save_conversation(conversation)
        
        logger.info(f"Added {role} message to conversation {conversation_id}")
        return conversation
    
    @log_execution_time(logger)
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
            
        Raises:
            ResourceNotFoundError: If the conversation does not exist
            ServiceError: If the summary cannot be generated
        """
        if not self._initialized:
            await self.initialize()
        
        # Get conversation
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            logger.error(f"Conversation {conversation_id} not found")
            raise ResourceNotFoundError(f"Conversation {conversation_id} not found")
        
        logger.info(f"Generating summary for conversation {conversation_id}")
        
        try:
            # Extract categories covered
            categories_covered = set()
            for message in conversation.messages:
                if message.metadata and "category" in message.metadata:
                    categories_covered.add(message.metadata["category"])
            
            # Use the information extractor if available
            extracted_info = {}
            if self._extractor:
                try:
                    extracted_info = await self._extractor.extract_conversation_information(conversation)
                except Exception as e:
                    logger.error(f"Error extracting information: {str(e)}")
                    # Continue with empty extracted info
            
            # Generate summary using AI
            conversation_text = "\n".join([
                f"{msg.role}: {msg.content}"
                for msg in conversation.messages
            ])
            
            prompt = CONVERSATION_SUMMARY_PROMPT.format(
                conversation_messages=conversation_text
            )
            
            summary_result = await self._client.generate_structured_output(
                messages=[
                    {"role": "system", "content": "You are a conversation summarizer."},
                    {"role": "user", "content": prompt}
                ],
                response_schema={
                    "type": "object",
                    "properties": {
                        "summary_text": {"type": "string"},
                        "key_insights": {"type": "array", "items": {"type": "string"}},
                        "categories_summary": {"type": "object"},
                        "completion_percentage": {"type": "number", "minimum": 0, "maximum": 100},
                        "missing_information": {"type": "array", "items": {"type": "string"}},
                        "next_steps": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["summary_text", "completion_percentage"]
                }
            )
            
            # Create summary with AI-generated content
            summary = ConversationSummary(
                conversation_id=conversation_id,
                user_id=conversation.user_id,
                message_count=len(conversation.messages),
                categories_covered=list(categories_covered),
                extracted_info=extracted_info,
                completion_percentage=summary_result.get("completion_percentage", 0.0),
                summary_text=summary_result.get("summary_text", ""),
                generated_at=datetime.now(timezone.utc)
            )
            
            logger.info(f"Generated summary for conversation {conversation_id}")
            return summary
            
        except Exception as e:
            logger.exception(f"Error generating summary: {str(e)}")
            raise ServiceError(f"Failed to generate summary: {str(e)}")
    
    @log_execution_time(logger)
    async def clear_conversation(
        self,
        conversation_id: str
    ) -> None:
        """
        Clear a conversation's messages.
        
        Args:
            conversation_id: The conversation's ID
            
        Raises:
            ResourceNotFoundError: If the conversation does not exist
        """
        if not self._initialized:
            await self.initialize()
        
        # Get conversation
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            logger.error(f"Conversation {conversation_id} not found")
            raise ResourceNotFoundError(f"Conversation {conversation_id} not found")
        
        # Clear messages
        conversation.messages = []
        conversation.questions_asked = []
        conversation.answers_received = []
        
        # Update last_updated timestamp
        conversation.last_updated = datetime.now(timezone.utc)
        
        # Save updated conversation
        await self._save_conversation(conversation)
        
        logger.info(f"Cleared messages from conversation {conversation_id}") 