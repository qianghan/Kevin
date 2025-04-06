"""
Question generator implementation.

This module implements the IQuestionGenerator interface to generate
questions for profile building based on user data.
"""

import uuid
from typing import Dict, List, Any, Optional
import json

from ...utils.logging import get_logger, log_execution_time
from ...utils.errors import ValidationError, ServiceError
from ...core.interfaces import AIClientInterface
from .interfaces import IQuestionGenerator 
from .models import Question, Answer, QuestionCategory
from .templates import QUESTION_GENERATION_PROMPT, FOLLOW_UP_PROMPT

logger = get_logger(__name__)

class AIQuestionGenerator(IQuestionGenerator):
    """
    Question generator implementation using AI models.
    
    This class generates questions for profile building using an AI model.
    It follows the Single Responsibility Principle by focusing solely on
    question generation.
    """
    
    def __init__(self, ai_client: AIClientInterface):
        """
        Initialize the question generator.
        
        Args:
            ai_client: Client for AI model interactions
        """
        self._client = ai_client
        self._initialized = False
        logger.info("Initialized AIQuestionGenerator")
    
    async def initialize(self) -> None:
        """Initialize the question generator."""
        if not self._initialized:
            logger.info("Initializing question generator")
            self._initialized = True
    
    async def shutdown(self) -> None:
        """Shutdown the question generator and release resources."""
        if self._initialized:
            logger.info("Shutting down question generator")
            self._initialized = False
    
    @log_execution_time(logger)
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
            
        Raises:
            ValidationError: If the profile data is invalid
            ServiceError: If questions cannot be generated
        """
        if not self._initialized:
            await self.initialize()
        
        if not profile_data:
            logger.error("Empty profile data provided")
            raise ValidationError("Profile data cannot be empty")
        
        # Filter categories if specified
        valid_categories = [c.value for c in QuestionCategory.__members__.values()]
        target_categories = categories or valid_categories
        
        # Validate categories
        invalid_categories = [c for c in target_categories if c not in valid_categories]
        if invalid_categories:
            logger.warning(f"Invalid categories specified: {invalid_categories}")
            target_categories = [c for c in target_categories if c in valid_categories]
        
        if not target_categories:
            logger.error("No valid categories specified")
            raise ValidationError("At least one valid category must be specified")
        
        try:
            logger.info(f"Generating {count} questions for categories: {target_categories}")
            
            # Prepare prompt
            prompt = QUESTION_GENERATION_PROMPT.format(
                profile_data=json.dumps(profile_data),
                categories=json.dumps(target_categories),
                count=count
            )
            
            # Generate questions using AI
            response = await self._client.generate_structured_output(
                messages=[
                    {"role": "system", "content": "You are a profile question generator."},
                    {"role": "user", "content": prompt}
                ],
                response_schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "enum": valid_categories},
                            "question_text": {"type": "string"},
                            "expected_response_type": {"type": "string"},
                            "required": {"type": "boolean"},
                            "follow_up_questions": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["category", "question_text", "expected_response_type"]
                    }
                }
            )
            
            # Convert to Question objects
            questions = []
            for i, item in enumerate(response):
                try:
                    # Generate unique ID
                    question_id = f"q_{uuid.uuid4().hex[:8]}"
                    
                    # Create Question object
                    question = Question(
                        question_id=question_id,
                        category=item["category"],
                        question_text=item["question_text"],
                        expected_response_type=item["expected_response_type"],
                        required=item.get("required", True),
                        follow_up_questions=item.get("follow_up_questions", []),
                        context={"generated_from": profile_data.get("user_id", "unknown")}
                    )
                    
                    questions.append(question)
                except Exception as e:
                    logger.error(f"Error creating question from item {i}: {str(e)}")
            
            logger.info(f"Generated {len(questions)} questions")
            return questions
            
        except Exception as e:
            logger.exception(f"Error generating questions: {str(e)}")
            raise ServiceError(f"Failed to generate questions: {str(e)}")
    
    @log_execution_time(logger)
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
            
        Raises:
            ValidationError: If the inputs are invalid
            ServiceError: If follow-up questions cannot be generated
        """
        if not self._initialized:
            await self.initialize()
        
        if not answer.response:
            logger.error("Empty answer response provided")
            raise ValidationError("Answer response cannot be empty")
        
        try:
            logger.info(f"Generating follow-up questions for question: {question.question_id}")
            
            # Prepare prompt
            prompt = FOLLOW_UP_PROMPT.format(
                original_question=question.question_text,
                answer=answer.response,
                profile_data=json.dumps(profile_data),
                category=question.category
            )
            
            # Generate follow-up questions using AI
            response = await self._client.generate_structured_output(
                messages=[
                    {"role": "system", "content": "You are a profile question generator."},
                    {"role": "user", "content": prompt}
                ],
                response_schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question_text": {"type": "string"},
                            "expected_response_type": {"type": "string"},
                            "required": {"type": "boolean"}
                        },
                        "required": ["question_text", "expected_response_type"]
                    }
                }
            )
            
            # Convert to Question objects
            follow_up_questions = []
            for i, item in enumerate(response):
                try:
                    # Generate unique ID
                    question_id = f"q_{uuid.uuid4().hex[:8]}"
                    
                    # Create Question object
                    follow_up = Question(
                        question_id=question_id,
                        category=question.category,
                        question_text=item["question_text"],
                        expected_response_type=item["expected_response_type"],
                        required=item.get("required", False),
                        follow_up_questions=[],
                        context={
                            "parent_question_id": question.question_id,
                            "parent_answer": answer.response
                        }
                    )
                    
                    follow_up_questions.append(follow_up)
                except Exception as e:
                    logger.error(f"Error creating follow-up question from item {i}: {str(e)}")
            
            logger.info(f"Generated {len(follow_up_questions)} follow-up questions")
            return follow_up_questions
            
        except Exception as e:
            logger.exception(f"Error generating follow-up questions: {str(e)}")
            raise ServiceError(f"Failed to generate follow-up questions: {str(e)}")

class TemplateBankQuestionGenerator(IQuestionGenerator):
    """
    Question generator implementation using a bank of question templates.
    
    This class demonstrates the Open-Closed Principle by providing an
    alternative implementation that doesn't require an AI model.
    """
    
    def __init__(self, question_templates: Dict[str, List[Dict[str, Any]]]):
        """
        Initialize the question generator with templates.
        
        Args:
            question_templates: Dictionary mapping categories to lists of question templates
        """
        self._templates = question_templates
        self._initialized = False
        logger.info(f"Initialized TemplateBankQuestionGenerator with {sum(len(v) for v in question_templates.values())} templates")
    
    async def initialize(self) -> None:
        """Initialize the question generator."""
        if not self._initialized:
            logger.info("Initializing template bank question generator")
            self._initialized = True
    
    async def shutdown(self) -> None:
        """Shutdown the question generator and release resources."""
        if self._initialized:
            logger.info("Shutting down template bank question generator")
            self._initialized = False
    
    @log_execution_time(logger)
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
        if not self._initialized:
            await self.initialize()
        
        # Filter categories if specified
        valid_categories = [c.value for c in QuestionCategory.__members__.values()]
        target_categories = categories or valid_categories
        
        # Get templates for selected categories
        available_templates = {}
        for category in target_categories:
            if category in self._templates:
                available_templates[category] = self._templates[category]
        
        if not available_templates:
            logger.warning("No templates available for selected categories")
            return []
        
        # Select templates based on profile data and count
        selected_questions = []
        remaining_count = count
        
        # Distribute count evenly among categories
        count_per_category = max(1, remaining_count // len(available_templates))
        
        for category, templates in available_templates.items():
            # Select most relevant templates for this category
            category_templates = self._select_templates(templates, profile_data, count_per_category)
            
            # Create Question objects
            for template in category_templates:
                question_id = f"q_{uuid.uuid4().hex[:8]}"
                question = Question(
                    question_id=question_id,
                    category=category,
                    question_text=template["question_text"],
                    expected_response_type=template["expected_response_type"],
                    required=template.get("required", True),
                    follow_up_questions=template.get("follow_up_questions", []),
                    context={"template_id": template.get("id", "unknown")}
                )
                selected_questions.append(question)
                remaining_count -= 1
                
                if remaining_count <= 0:
                    break
            
            if remaining_count <= 0:
                break
        
        logger.info(f"Generated {len(selected_questions)} questions from templates")
        return selected_questions
    
    def _select_templates(
        self,
        templates: List[Dict[str, Any]],
        profile_data: Dict[str, Any],
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Select the most relevant templates for the given profile data.
        
        Args:
            templates: List of question templates
            profile_data: The user's profile data
            count: Number of templates to select
            
        Returns:
            List of selected templates
        """
        # Simple selection - could be improved with more sophisticated relevance scoring
        # For now, just select the first N templates
        return templates[:count]
    
    @log_execution_time(logger)
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
        if not self._initialized:
            await self.initialize()
        
        # Get follow-up questions from the original question
        if not question.follow_up_questions:
            return []
        
        # Create Question objects from follow-up question strings
        follow_up_questions = []
        for follow_up_text in question.follow_up_questions:
            question_id = f"q_{uuid.uuid4().hex[:8]}"
            follow_up = Question(
                question_id=question_id,
                category=question.category,
                question_text=follow_up_text,
                expected_response_type="text",  # Default response type
                required=False,
                follow_up_questions=[],
                context={
                    "parent_question_id": question.question_id,
                    "parent_answer": answer.response
                }
            )
            follow_up_questions.append(follow_up)
        
        logger.info(f"Generated {len(follow_up_questions)} follow-up questions from templates")
        return follow_up_questions 