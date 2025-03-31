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

__all__ = [
    'QAService',
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