"""
Information extractor implementation.

This module implements the IInformationExtractor interface to extract
structured information from answers and conversations.
"""

from typing import Dict, List, Any, Optional
import json
import re

from ...utils.logging import get_logger, log_execution_time
from ...utils.errors import ValidationError, ServiceError
from ...utils.cache import cache_async
from ...core.interfaces import AIClientInterface
from ..interfaces import IInformationExtractor
from .models import Question, Answer, Conversation, QuestionCategory
from .templates import INFORMATION_EXTRACTION_PROMPT

logger = get_logger(__name__)

class AIInformationExtractor(IInformationExtractor):
    """
    Information extractor implementation using AI models.
    
    This class extracts structured information from answers using an AI model.
    It follows the Single Responsibility Principle by focusing solely on
    information extraction.
    """
    
    def __init__(self, ai_client: AIClientInterface):
        """
        Initialize the information extractor.
        
        Args:
            ai_client: Client for AI model interactions
        """
        self._client = ai_client
        self._initialized = False
        logger.info("Initialized AIInformationExtractor")
    
    async def initialize(self) -> None:
        """Initialize the information extractor."""
        if not self._initialized:
            logger.info("Initializing information extractor")
            self._initialized = True
    
    async def shutdown(self) -> None:
        """Shutdown the information extractor and release resources."""
        if self._initialized:
            logger.info("Shutting down information extractor")
            self._initialized = False
    
    @log_execution_time(logger)
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
            
        Raises:
            ValidationError: If the inputs are invalid
            ServiceError: If the extraction fails
        """
        if not self._initialized:
            await self.initialize()
        
        if not answer.response:
            logger.error("Empty answer response provided")
            raise ValidationError("Answer response cannot be empty")
        
        try:
            logger.info(f"Extracting information from answer to question: {question.question_id}")
            
            # Prepare prompt
            prompt = INFORMATION_EXTRACTION_PROMPT.format(
                question_text=question.question_text,
                category=question.category,
                expected_response_type=question.expected_response_type,
                answer_text=answer.response
            )
            
            # Extract information using AI
            extraction_result = await self._client.generate_structured_output(
                messages=[
                    {"role": "system", "content": "You are a profile information extractor."},
                    {"role": "user", "content": prompt}
                ],
                response_schema=self._get_schema_for_category(question.category)
            )
            
            logger.info(f"Successfully extracted information from answer to question: {question.question_id}")
            return extraction_result
            
        except Exception as e:
            logger.exception(f"Error extracting information: {str(e)}")
            raise ServiceError(f"Failed to extract information: {str(e)}")
    
    @log_execution_time(logger)
    @cache_async(ttl=300)  # Cache results for 5 minutes
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
            
        Raises:
            ValidationError: If the inputs are invalid
            ServiceError: If the extraction fails
        """
        if not self._initialized:
            await self.initialize()
        
        if not conversation.messages:
            logger.error("Empty conversation messages provided")
            raise ValidationError("Conversation messages cannot be empty")
        
        try:
            logger.info(f"Extracting information from conversation: {conversation.conversation_id}")
            
            # Group messages by category
            messages_by_category = {}
            
            for i, q_id in enumerate(conversation.questions_asked):
                if i < len(conversation.answers_received):
                    # Find the question and answer
                    question_text = ""
                    answer_text = ""
                    category = "general"
                    
                    # This would normally use a repository to fetch questions and answers
                    # For now, we'll extract them from the messages
                    for msg in conversation.messages:
                        if msg.metadata and msg.metadata.get("question_id") == q_id:
                            question_text = msg.content
                            category = msg.metadata.get("category", "general")
                        elif msg.metadata and msg.metadata.get("answer_id") == conversation.answers_received[i]:
                            answer_text = msg.content
                    
                    if question_text and answer_text:
                        if category not in messages_by_category:
                            messages_by_category[category] = []
                        
                        messages_by_category[category].append({
                            "question": question_text,
                            "answer": answer_text
                        })
            
            # Extract information for each category
            result = {}
            
            for category, qa_pairs in messages_by_category.items():
                # Combine all Q&A pairs for this category
                combined_text = "\n\n".join([
                    f"Q: {pair['question']}\nA: {pair['answer']}"
                    for pair in qa_pairs
                ])
                
                # Create a synthetic question and answer for extraction
                synthetic_question = Question(
                    question_id="synthetic",
                    category=category,
                    question_text=f"Tell me about your {category} background",
                    expected_response_type="text",
                    required=False,
                    follow_up_questions=[]
                )
                
                synthetic_answer = Answer(
                    question_id="synthetic",
                    response=combined_text
                )
                
                # Extract information
                category_info = await self.extract_information(
                    synthetic_question,
                    synthetic_answer
                )
                
                result[category] = category_info
            
            logger.info(f"Successfully extracted information from conversation: {conversation.conversation_id}")
            return result
            
        except Exception as e:
            logger.exception(f"Error extracting conversation information: {str(e)}")
            raise ServiceError(f"Failed to extract conversation information: {str(e)}")
    
    def _get_schema_for_category(self, category: str) -> Dict[str, Any]:
        """
        Get the JSON schema for a specific category.
        
        Args:
            category: The category to get schema for
            
        Returns:
            JSON schema for the category
        """
        # Define schemas for each category
        schemas = {
            "academic": {
                "type": "object",
                "properties": {
                    "subjects": {"type": "array", "items": {"type": "string"}},
                    "grades": {"type": "array", "items": {"type": "string"}},
                    "achievements": {"type": "array", "items": {"type": "string"}},
                    "institutions": {"type": "array", "items": {"type": "string"}},
                    "skills": {"type": "array", "items": {"type": "string"}},
                    "interests": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["subjects", "grades", "achievements"]
            },
            "extracurricular": {
                "type": "object",
                "properties": {
                    "activities": {"type": "array", "items": {"type": "string"}},
                    "roles": {"type": "array", "items": {"type": "string"}},
                    "timeframes": {"type": "array", "items": {"type": "string"}},
                    "achievements": {"type": "array", "items": {"type": "string"}},
                    "skills": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["activities"]
            },
            "personal": {
                "type": "object",
                "properties": {
                    "background": {"type": "object"},
                    "values": {"type": "array", "items": {"type": "string"}},
                    "strengths": {"type": "array", "items": {"type": "string"}},
                    "challenges": {"type": "array", "items": {"type": "string"}},
                    "interests": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["strengths", "interests"]
            },
            "essays": {
                "type": "object",
                "properties": {
                    "topics": {"type": "array", "items": {"type": "string"}},
                    "themes": {"type": "array", "items": {"type": "string"}},
                    "strengths": {"type": "array", "items": {"type": "string"}},
                    "areas_for_improvement": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["topics"]
            },
            "goals": {
                "type": "object",
                "properties": {
                    "short_term": {"type": "array", "items": {"type": "string"}},
                    "long_term": {"type": "array", "items": {"type": "string"}},
                    "career": {"type": "array", "items": {"type": "string"}},
                    "academic": {"type": "array", "items": {"type": "string"}},
                    "personal": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["career"]
            }
        }
        
        # Return schema for category, or a default schema
        return schemas.get(category, {
            "type": "object",
            "properties": {
                "key_points": {"type": "array", "items": {"type": "string"}},
                "extracted_data": {"type": "object"}
            },
            "required": ["key_points"]
        })

class PatternBasedExtractor(IInformationExtractor):
    """
    Information extractor implementation using regex patterns.
    
    This class demonstrates the Open-Closed Principle by providing an
    alternative implementation that doesn't require an AI model.
    """
    
    def __init__(self, patterns: Optional[Dict[str, Dict[str, List[re.Pattern]]]] = None):
        """
        Initialize the pattern-based extractor.
        
        Args:
            patterns: Optional dictionary of regex patterns by category and field
        """
        self._patterns = patterns or self._get_default_patterns()
        self._initialized = False
        logger.info("Initialized PatternBasedExtractor")
    
    async def initialize(self) -> None:
        """Initialize the information extractor."""
        if not self._initialized:
            logger.info("Initializing pattern-based information extractor")
            self._initialized = True
    
    async def shutdown(self) -> None:
        """Shutdown the information extractor and release resources."""
        if self._initialized:
            logger.info("Shutting down pattern-based information extractor")
            self._initialized = False
    
    @log_execution_time(logger)
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
        if not self._initialized:
            await self.initialize()
        
        response_str = str(answer.response)
        category = question.category
        
        # Get patterns for this category
        category_patterns = self._patterns.get(category, {})
        
        # Extract information using patterns
        result = {}
        
        for field, patterns in category_patterns.items():
            extracted_values = []
            
            for pattern in patterns:
                matches = pattern.findall(response_str)
                for match in matches:
                    # Handle both single groups and multiple groups
                    if isinstance(match, tuple):
                        # Use the first non-empty group
                        value = next((g for g in match if g), "")
                    else:
                        value = match
                    
                    value = value.strip()
                    if value and value not in extracted_values:
                        extracted_values.append(value)
            
            result[field] = extracted_values
        
        logger.info(f"Extracted information from answer using patterns: {len(result)} fields")
        return result
    
    @log_execution_time(logger)
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
        if not self._initialized:
            await self.initialize()
        
        # Combine all messages
        combined_text = "\n".join([msg.content for msg in conversation.messages])
        
        # Extract information for each category
        result = {}
        
        for category, field_patterns in self._patterns.items():
            category_result = {}
            
            for field, patterns in field_patterns.items():
                extracted_values = []
                
                for pattern in patterns:
                    matches = pattern.findall(combined_text)
                    for match in matches:
                        # Handle both single groups and multiple groups
                        if isinstance(match, tuple):
                            # Use the first non-empty group
                            value = next((g for g in match if g), "")
                        else:
                            value = match
                        
                        value = value.strip()
                        if value and value not in extracted_values:
                            extracted_values.append(value)
                
                category_result[field] = extracted_values
            
            result[category] = category_result
        
        logger.info(f"Extracted information from conversation using patterns: {len(result)} categories")
        return result
    
    def _get_default_patterns(self) -> Dict[str, Dict[str, List[re.Pattern]]]:
        """
        Get default regex patterns for information extraction.
        
        Returns:
            Dictionary of regex patterns by category and field
        """
        patterns = {
            "academic": {
                "subjects": [
                    re.compile(r"(?:favorite|preferred|liked) subjects?(?:\s+were|\s+was|\s+are|\s+is)?\s+([^.,:;]+)"),
                    re.compile(r"(?:studied|studying|taking|took)\s+([^.,:;]+)")
                ],
                "grades": [
                    re.compile(r"(?:GPA|grade point average)(?:\s+was|\s+is|\s+of)?\s+([\d.]+)"),
                    re.compile(r"grades?(?:\s+were|\s+was|\s+are|\s+is)?\s+([^.,:;]+)")
                ],
                "achievements": [
                    re.compile(r"(?:received|earned|won|awarded|achieved)\s+([^.,:;]+)"),
                    re.compile(r"(?:achievements?|awards?)(?:\s+include|\s+included|\s+are|\s+is)?\s+([^.,:;]+)")
                ],
                "institutions": [
                    re.compile(r"(?:attend(?:ed|ing)?|enrolled|graduated from)\s+([^.,:;]+)(?:\s+(?:University|College|School|Institute|Academy))?"),
                    re.compile(r"(?:University|College|School|Institute|Academy) of ([^.,:;]+)")
                ]
            },
            "extracurricular": {
                "activities": [
                    re.compile(r"(?:activities|extracurriculars|clubs)(?:\s+include|\s+included|\s+are|\s+is)?\s+([^.,:;]+)"),
                    re.compile(r"(?:participated|involved|engaged)(?:\s+in)?\s+([^.,:;]+)")
                ],
                "roles": [
                    re.compile(r"(?:role|position|title)(?:\s+as|\s+of|\s+was|\s+is)?\s+([^.,:;]+)"),
                    re.compile(r"(?:served|serving|acted|acting)(?:\s+as)?\s+(?:the|a)?\s+([^.,:;]+)")
                ],
                "timeframes": [
                    re.compile(r"(?:for|during)(?:\s+the)?\s+(?:past|last)?\s+(\d+\s+(?:year|month|week|day)s?)"),
                    re.compile(r"(?:since|from)\s+(\d{4}|\w+ \d{4})")
                ]
            },
            "personal": {
                "strengths": [
                    re.compile(r"(?:strengths|strong points|good at)(?:\s+are|\s+is|\s+include|\s+included)?\s+([^.,:;]+)"),
                    re.compile(r"(?:I am|I'm)(?:\s+particularly)?\s+(?:good|great|excellent|skilled|proficient)(?:\s+at)?\s+([^.,:;]+)")
                ],
                "challenges": [
                    re.compile(r"(?:challenges|difficulties|struggled with)(?:\s+were|\s+was|\s+are|\s+is|\s+included)?\s+([^.,:;]+)"),
                    re.compile(r"(?:overcome|faced|dealt with|worked through)\s+([^.,:;]+)")
                ],
                "interests": [
                    re.compile(r"(?:interests|hobbies|passion)(?:\s+are|\s+is|\s+include|\s+included)?\s+([^.,:;]+)"),
                    re.compile(r"(?:interested|passionate)(?:\s+in|\s+about)?\s+([^.,:;]+)")
                ]
            }
        }
        
        return patterns 