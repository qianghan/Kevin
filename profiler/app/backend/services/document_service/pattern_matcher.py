"""
Pattern matcher implementation for the Document Service.

This module provides implementations of the PatternMatcherInterface for matching patterns in documents.
"""

import re
from typing import Dict, Any, List, Match, Optional, Pattern as RegexPattern
import logging
from .interfaces import PatternMatcherInterface

# Get logger
logger = logging.getLogger(__name__)

class RegexPatternMatcher(PatternMatcherInterface):
    """Implementation of PatternMatcherInterface using regular expressions"""
    
    def __init__(self):
        self._compiled_patterns: Dict[str, RegexPattern] = {}
    
    async def match_patterns(self, content: str, patterns: Dict[str, str]) -> Dict[str, List[Any]]:
        """
        Match patterns in the document content using regular expressions.
        
        Args:
            content: The document content
            patterns: Dictionary of named patterns
            
        Returns:
            Dictionary of pattern matches
        """
        results = {}
        
        for name, pattern in patterns.items():
            try:
                # Compile the pattern if not already compiled
                if pattern not in self._compiled_patterns:
                    self._compiled_patterns[pattern] = re.compile(pattern)
                
                # Find all matches
                compiled_pattern = self._compiled_patterns[pattern]
                matches = list(compiled_pattern.finditer(content))
                
                # Store the match objects
                results[name] = matches
                
                logger.debug(f"Pattern '{name}' matched {len(matches)} times")
                
            except re.error as e:
                logger.error(f"Invalid regex pattern '{name}': {e}")
                results[name] = []
        
        return results
    
    def get_match_groups(self, match: Match, group_names: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Extract named groups from a match object.
        
        Args:
            match: The regex match object
            group_names: Optional list of group names to extract
            
        Returns:
            Dictionary of group names and their values
        """
        if group_names:
            return {name: match.group(i+1) for i, name in enumerate(group_names) if i+1 <= len(match.groups())}
        
        # If no group names provided, use numbered groups
        return {str(i): match.group(i) for i in range(1, len(match.groups()) + 1)}

class DocumentPatternLibrary:
    """Library of common document patterns"""
    
    # Transcript patterns
    TRANSCRIPT_PATTERNS = {
        "grade_pattern": r"([A-Z][+-]?)\s*(\d{1,2}(?:\.\d{1,2})?)",
        "course_pattern": r"([A-Z]{2,4}\s*\d{3,4}[A-Z]?)\s*([^0-9]+)",
        "term_pattern": r"(Fall|Spring|Summer|Winter)\s*(\d{4})",
        "gpa_pattern": r"GPA:\s*(\d+\.\d+)|Cumulative GPA:\s*(\d+\.\d+)"
    }
    
    # Essay patterns
    ESSAY_PATTERNS = {
        "word_count_pattern": r"\b\w+\b",
        "paragraph_pattern": r"\n\s*\n",
        "citation_pattern": r"\(([^)]+),\s*(\d{4})\)|^\s*\d+\.\s*([^.]+)\.",
        "heading_pattern": r"^(#+)\s+(.+)$|^(.+)\n([-=]+)$"
    }
    
    # Resume patterns
    RESUME_PATTERNS = {
        "section_pattern": r"^([A-Z][A-Za-z\s]+):",
        "date_pattern": r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4}",
        "skill_pattern": r"Skills:(.+?)(?:\n\n|\Z)",
        "education_pattern": r"(?:Education|EDUCATION)(.+?)(?:\n\n|\Z)",
        "experience_pattern": r"(?:Experience|EXPERIENCE|Work Experience|WORK EXPERIENCE)(.+?)(?:\n\n|\Z)",
    }
    
    # Letter patterns
    LETTER_PATTERNS = {
        "greeting_pattern": r"Dear\s+([^,]+),",
        "closing_pattern": r"(Sincerely|Regards|Yours truly|Best regards|Respectfully),\s*\n+([^,\n]+)",
        "date_pattern": r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}"
    }
    
    @classmethod
    def get_patterns_for_document_type(cls, document_type: str) -> Dict[str, str]:
        """
        Get patterns for a specific document type.
        
        Args:
            document_type: The document type
            
        Returns:
            Dictionary of patterns for the document type
        """
        type_map = {
            "transcript": cls.TRANSCRIPT_PATTERNS,
            "essay": cls.ESSAY_PATTERNS,
            "resume": cls.RESUME_PATTERNS,
            "letter": cls.LETTER_PATTERNS
        }
        
        return type_map.get(document_type, {}) 