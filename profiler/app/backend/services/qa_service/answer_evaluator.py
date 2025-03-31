"""
Answer evaluator implementation.

This module implements the IAnswerEvaluator interface to evaluate
the quality of answers to profile questions.
"""

from typing import Dict, List, Any, Optional
import json
import statistics

from ...utils.logging import get_logger, log_execution_time
from ...utils.errors import ValidationError, ServiceError
from ...core.interfaces import AIClientInterface
from ..interfaces import IAnswerEvaluator
from .models import Question, Answer
from .templates import ANSWER_EVALUATION_PROMPT

logger = get_logger(__name__)

class AIAnswerEvaluator(IAnswerEvaluator):
    """
    Answer evaluator implementation using AI models.
    
    This class evaluates the quality of answers to profile questions using an AI model.
    It follows the Single Responsibility Principle by focusing solely on answer evaluation.
    """
    
    def __init__(self, ai_client: AIClientInterface):
        """
        Initialize the answer evaluator.
        
        Args:
            ai_client: Client for AI model interactions
        """
        self._client = ai_client
        self._initialized = False
        logger.info("Initialized AIAnswerEvaluator")
    
    async def initialize(self) -> None:
        """Initialize the answer evaluator."""
        if not self._initialized:
            logger.info("Initializing answer evaluator")
            self._initialized = True
    
    async def shutdown(self) -> None:
        """Shutdown the answer evaluator and release resources."""
        if self._initialized:
            logger.info("Shutting down answer evaluator")
            self._initialized = False
    
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
            logger.info(f"Evaluating answer to question: {question.question_id}")
            
            # Prepare prompt
            prompt = ANSWER_EVALUATION_PROMPT.format(
                question_text=question.question_text,
                category=question.category,
                expected_response_type=question.expected_response_type,
                answer_text=answer.response
            )
            
            # Evaluate answer using AI
            evaluation = await self._client.generate_structured_output(
                messages=[
                    {"role": "system", "content": "You are a profile answer evaluator."},
                    {"role": "user", "content": prompt}
                ],
                response_schema={
                    "type": "object",
                    "properties": {
                        "quality_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "completeness": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "relevance": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "specificity": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "helpfulness": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "authenticity": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "needs_follow_up": {"type": "boolean"},
                        "feedback": {"type": "string"}
                    },
                    "required": ["quality_score", "needs_follow_up"]
                }
            )
            
            # Update answer with evaluation
            updated_answer = answer.copy()
            updated_answer.quality_score = evaluation.get("quality_score", 0.5)
            updated_answer.needs_follow_up = evaluation.get("needs_follow_up", False)
            
            # Add evaluation details to metadata
            if updated_answer.metadata is None:
                updated_answer.metadata = {}
            
            updated_answer.metadata["evaluation"] = {
                "completeness": evaluation.get("completeness"),
                "relevance": evaluation.get("relevance"),
                "specificity": evaluation.get("specificity"),
                "helpfulness": evaluation.get("helpfulness"),
                "authenticity": evaluation.get("authenticity"),
                "feedback": evaluation.get("feedback")
            }
            
            logger.info(f"Answer evaluation complete: quality_score={updated_answer.quality_score}, needs_follow_up={updated_answer.needs_follow_up}")
            return updated_answer
            
        except Exception as e:
            logger.exception(f"Error evaluating answer: {str(e)}")
            raise ServiceError(f"Failed to evaluate answer: {str(e)}")
    
    @log_execution_time(logger)
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
            
        Raises:
            ValidationError: If the inputs are invalid
        """
        if not self._initialized:
            await self.initialize()
        
        if not answer.response:
            logger.error("Empty answer response provided")
            raise ValidationError("Answer response cannot be empty")
        
        # If already evaluated, use the existing evaluation
        if answer.metadata and "evaluation" in answer.metadata:
            return not answer.needs_follow_up
        
        # Simple heuristic-based check
        response_str = str(answer.response)
        
        # Check 1: Minimum length requirement
        min_length = 10
        if len(response_str) < min_length:
            logger.info(f"Answer too short ({len(response_str)} chars), needs follow-up")
            return False
        
        # Check 2: Response type match
        if question.expected_response_type == "number":
            # Check if response contains at least one number
            if not any(c.isdigit() for c in response_str):
                logger.info("Number expected but none found in answer, needs follow-up")
                return False
        
        # Check 3: Question complexity vs. answer length
        question_words = len(question.question_text.split())
        answer_words = len(response_str.split())
        
        if question_words > 10 and answer_words < 5:
            logger.info(f"Complex question ({question_words} words) with short answer ({answer_words} words), needs follow-up")
            return False
        
        # Default to complete
        logger.info("Answer appears complete based on heuristic checks")
        return True

class RuleBasedAnswerEvaluator(IAnswerEvaluator):
    """
    Answer evaluator implementation using rule-based heuristics.
    
    This class demonstrates the Open-Closed Principle by providing an
    alternative implementation that doesn't require an AI model.
    """
    
    def __init__(self, rules: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize the rule-based evaluator.
        
        Args:
            rules: Optional dictionary of evaluation rules by category
        """
        self._rules = rules or {}
        self._initialized = False
        logger.info("Initialized RuleBasedAnswerEvaluator")
    
    async def initialize(self) -> None:
        """Initialize the answer evaluator."""
        if not self._initialized:
            logger.info("Initializing rule-based answer evaluator")
            self._initialized = True
    
    async def shutdown(self) -> None:
        """Shutdown the answer evaluator and release resources."""
        if self._initialized:
            logger.info("Shutting down rule-based answer evaluator")
            self._initialized = False
    
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
        """
        if not self._initialized:
            await self.initialize()
        
        response_str = str(answer.response)
        category = question.category
        
        # Get category-specific rules
        category_rules = self._rules.get(category, {})
        
        # Calculate scores
        scores = {}
        
        # Completeness score
        min_word_count = category_rules.get("min_word_count", 5)
        target_word_count = category_rules.get("target_word_count", 20)
        word_count = len(response_str.split())
        
        if word_count < min_word_count:
            scores["completeness"] = 0.0
        elif word_count >= target_word_count:
            scores["completeness"] = 1.0
        else:
            scores["completeness"] = (word_count - min_word_count) / (target_word_count - min_word_count)
        
        # Relevance score (simple keyword matching)
        relevant_keywords = category_rules.get("relevant_keywords", [])
        if relevant_keywords:
            matches = sum(1 for keyword in relevant_keywords if keyword.lower() in response_str.lower())
            scores["relevance"] = min(1.0, matches / max(1, len(relevant_keywords) / 3))
        else:
            scores["relevance"] = 0.5  # Default relevance
        
        # Specificity score (look for specific patterns)
        has_numbers = any(c.isdigit() for c in response_str)
        has_proper_nouns = any(word[0].isupper() for word in response_str.split() if len(word) > 1 and word[0].isalpha())
        specificity_indicators = [has_numbers, has_proper_nouns]
        scores["specificity"] = sum(1 for indicator in specificity_indicators if indicator) / len(specificity_indicators)
        
        # Overall quality score
        weights = {
            "completeness": 0.4,
            "relevance": 0.4,
            "specificity": 0.2
        }
        
        quality_score = sum(score * weights[metric] for metric, score in scores.items())
        
        # Determine if follow-up is needed
        needs_follow_up = quality_score < category_rules.get("follow_up_threshold", 0.6)
        
        # Update answer
        updated_answer = answer.copy()
        updated_answer.quality_score = quality_score
        updated_answer.needs_follow_up = needs_follow_up
        
        # Add evaluation details to metadata
        if updated_answer.metadata is None:
            updated_answer.metadata = {}
        
        updated_answer.metadata["evaluation"] = scores
        updated_answer.metadata["evaluation"]["method"] = "rule_based"
        
        logger.info(f"Rule-based evaluation complete: quality_score={quality_score}, needs_follow_up={needs_follow_up}")
        return updated_answer
    
    @log_execution_time(logger)
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
        if not self._initialized:
            await self.initialize()
        
        # If already evaluated, use the existing evaluation
        if answer.needs_follow_up is not None:
            return not answer.needs_follow_up
        
        response_str = str(answer.response)
        
        # Simple completion check
        min_word_count = self._rules.get(question.category, {}).get("min_word_count", 5)
        word_count = len(response_str.split())
        
        if word_count < min_word_count:
            logger.info(f"Answer too short ({word_count} words), needs follow-up")
            return False
        
        # Check expected response type
        if question.expected_response_type == "number" and not any(c.isdigit() for c in response_str):
            logger.info("Number expected but none found in answer, needs follow-up")
            return False
        
        if question.expected_response_type == "boolean" and not any(word.lower() in ["yes", "no", "true", "false"] for word in response_str.split()):
            logger.info("Boolean expected but not found in answer, needs follow-up")
            return False
        
        # Default to complete
        logger.info("Answer appears complete based on rule-based checks")
        return True 