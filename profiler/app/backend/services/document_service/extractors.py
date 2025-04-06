"""
Information extractors for the Document Service.

This module provides implementations of the InformationExtractorInterface
for extracting information from documents using different methods.
"""

import logging
from typing import Dict, Any, List, Optional
import re

from ...core.interfaces import AIClientInterface

from .interfaces import InformationExtractorInterface, PatternMatcherInterface
from .models import DocumentType
from .pattern_matcher import RegexPatternMatcher, DocumentPatternLibrary

# Get logger
logger = logging.getLogger(__name__)

class RegexExtractor(InformationExtractorInterface):
    """Extractor that uses regular expressions to extract basic information"""
    
    def __init__(self, pattern_matcher: PatternMatcherInterface):
        self.pattern_matcher = pattern_matcher
    
    async def extract_basic_info(self, content: str, document_type: DocumentType) -> Dict[str, Any]:
        """
        Extract basic information using patterns.
        
        Args:
            content: The document content
            document_type: Type of the document
            
        Returns:
            Dictionary of extracted information
        """
        # Get patterns for the document type
        patterns = DocumentPatternLibrary.get_patterns_for_document_type(document_type.value)
        
        if not patterns:
            logger.warning(f"No patterns defined for document type: {document_type}")
            return {"source_type": "regex"}
        
        # Match patterns
        match_results = await self.pattern_matcher.match_patterns(content, patterns)
        
        # Process matches based on document type
        info = {"source_type": "regex"}
        
        try:
            if document_type == DocumentType.TRANSCRIPT:
                self._process_transcript_matches(match_results, info)
            elif document_type == DocumentType.ESSAY:
                self._process_essay_matches(match_results, info, content)
            elif document_type == DocumentType.RESUME:
                self._process_resume_matches(match_results, info)
            elif document_type == DocumentType.LETTER:
                self._process_letter_matches(match_results, info)
        except Exception as e:
            logger.error(f"Error processing matches for {document_type}: {str(e)}")
        
        return info
    
    async def extract_advanced_info(self, content: str, document_type: DocumentType, 
                              basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Regex extractor does not provide advanced info extraction.
        This is handled by the LLM extractor.
        
        Args:
            content: The document content
            document_type: Type of the document
            basic_info: Previously extracted basic information
            
        Returns:
            Empty dictionary
        """
        return {}
    
    def _process_transcript_matches(self, matches: Dict[str, List[Any]], info: Dict[str, Any]) -> None:
        """Process transcript pattern matches"""
        # Extract grades
        if 'grade_pattern' in matches:
            info['grades'] = [
                {"grade": m.group(1), "score": float(m.group(2))}
                for m in matches['grade_pattern']
            ]
        
        # Extract courses
        if 'course_pattern' in matches:
            info['courses'] = [
                {"code": m.group(1), "name": m.group(2).strip()}
                for m in matches['course_pattern']
            ]
        
        # Extract terms
        if 'term_pattern' in matches:
            info['terms'] = [
                {"term": m.group(1), "year": int(m.group(2))}
                for m in matches['term_pattern']
            ]
        
        # Extract GPA
        if 'gpa_pattern' in matches and matches['gpa_pattern']:
            m = matches['gpa_pattern'][0]
            gpa = m.group(1) or m.group(2)
            if gpa:
                info['gpa'] = float(gpa)
    
    def _process_essay_matches(self, matches: Dict[str, List[Any]], info: Dict[str, Any], content: str) -> None:
        """Process essay pattern matches"""
        # Count words
        if 'word_count_pattern' in matches:
            words = re.findall(r'\b\w+\b', content)
            info['word_count'] = len(words)
        
        # Count paragraphs
        if 'paragraph_pattern' in matches:
            paragraphs = re.split(r'\n\s*\n', content)
            info['paragraph_count'] = len(paragraphs)
        
        # Extract citations
        if 'citation_pattern' in matches:
            info['citations'] = [
                m.group(0) for m in matches['citation_pattern']
            ]
        
        # Extract headings
        if 'heading_pattern' in matches:
            info['headings'] = [
                m.group(2) or m.group(3) for m in matches['heading_pattern']
            ]
    
    def _process_resume_matches(self, matches: Dict[str, List[Any]], info: Dict[str, Any]) -> None:
        """Process resume pattern matches"""
        # Extract sections
        if 'section_pattern' in matches:
            info['sections'] = [
                m.group(1).strip() for m in matches['section_pattern']
            ]
        
        # Extract dates
        if 'date_pattern' in matches:
            info['dates'] = [
                m.group(0) for m in matches['date_pattern']
            ]
    
    def _process_letter_matches(self, matches: Dict[str, List[Any]], info: Dict[str, Any]) -> None:
        """Process letter pattern matches"""
        # Extract greeting
        if 'greeting_pattern' in matches and matches['greeting_pattern']:
            info['greeting'] = matches['greeting_pattern'][0].group(1)
        
        # Extract closing
        if 'closing_pattern' in matches and matches['closing_pattern']:
            m = matches['closing_pattern'][0]
            info['closing'] = {
                'type': m.group(1),
                'name': m.group(2).strip() if m.group(2) else ""
            }
        
        # Extract date
        if 'date_pattern' in matches and matches['date_pattern']:
            info['date'] = matches['date_pattern'][0].group(0)

class LLMExtractor(InformationExtractorInterface):
    """Extractor that uses LLM for advanced information extraction"""
    
    def __init__(self, ai_client: AIClientInterface):
        self.ai_client = ai_client
    
    async def extract_basic_info(self, content: str, document_type: DocumentType) -> Dict[str, Any]:
        """
        LLM extractor does not provide basic info extraction.
        This is handled by the RegexExtractor.
        
        Args:
            content: The document content
            document_type: Type of the document
            
        Returns:
            Empty dictionary with source type
        """
        return {"source_type": "llm"}
    
    async def extract_advanced_info(self, content: str, document_type: DocumentType, 
                              basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract advanced information using LLM.
        
        Args:
            content: The document content
            document_type: Type of the document
            basic_info: Previously extracted basic information
            
        Returns:
            Dictionary of extracted advanced information
        """
        # Define extraction tasks based on document type
        extraction_tasks = {
            DocumentType.TRANSCRIPT: self._extract_transcript_insights,
            DocumentType.ESSAY: self._extract_essay_insights,
            DocumentType.RESUME: self._extract_resume_insights,
            DocumentType.LETTER: self._extract_letter_insights,
            DocumentType.OTHER: self._extract_generic_insights
        }
        
        # Get the appropriate extraction task
        extract_task = extraction_tasks.get(document_type, self._extract_generic_insights)
        
        try:
            # Execute the extraction task
            advanced_info = await extract_task(content, basic_info)
            advanced_info["source_type"] = "llm"
            return advanced_info
        except Exception as e:
            logger.error(f"Error extracting advanced info with LLM: {str(e)}")
            return {"source_type": "llm", "error": str(e)}
    
    async def _extract_transcript_insights(self, content: str, basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from transcript"""
        prompt = """
        Analyze this academic transcript and provide:
        1. Overall academic performance evaluation
        2. Course selection patterns and focus areas
        3. Areas of strength and weakness
        4. Academic trends over time
        
        Basic Information already extracted:
        {basic_info}
        
        Content:
        {content}
        
        Provide a structured JSON response with the following fields:
        - academic_performance: overall performance evaluation
        - course_patterns: identified patterns in course selection
        - strengths: list of academic strengths
        - weaknesses: list of areas for improvement
        - trends: academic trends over time
        - academic_standing: inferred academic standing
        """
        
        structured_output = await self.ai_client.generate_structured_output(
            prompt=prompt.format(content=content[:1000], basic_info=str(basic_info)),
            output_schema={
                "academic_performance": "string",
                "course_patterns": "string",
                "strengths": "array",
                "weaknesses": "array",
                "trends": "string",
                "academic_standing": "string"
            }
        )
        
        return structured_output
    
    async def _extract_essay_insights(self, content: str, basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from essay"""
        prompt = """
        Analyze this essay and provide:
        1. Main themes and arguments
        2. Writing style analysis
        3. Structure and organization assessment
        4. Quality of argumentation
        5. Vocabulary assessment
        
        Basic Information already extracted:
        {basic_info}
        
        Content:
        {content}
        
        Provide a structured JSON response with the following fields:
        - themes: list of main themes
        - writing_style: analysis of writing style
        - structure_quality: score from 0-10 on structure quality
        - argument_quality: score from 0-10 on quality of arguments
        - vocabulary_assessment: assessment of vocabulary usage
        - tone: overall tone of the essay
        """
        
        structured_output = await self.ai_client.generate_structured_output(
            prompt=prompt.format(content=content[:1000], basic_info=str(basic_info)),
            output_schema={
                "themes": "array",
                "writing_style": "string",
                "structure_quality": "number",
                "argument_quality": "number",
                "vocabulary_assessment": "string",
                "tone": "string"
            }
        )
        
        return structured_output
    
    async def _extract_resume_insights(self, content: str, basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from resume"""
        prompt = """
        Analyze this resume and provide:
        1. Key achievements and experiences
        2. Skills assessment
        3. Career progression
        4. Areas for enhancement
        5. Experience level
        
        Basic Information already extracted:
        {basic_info}
        
        Content:
        {content}
        
        Provide a structured JSON response with the following fields:
        - key_achievements: list of notable achievements
        - skills_assessment: assessment of skills
        - career_progression: analysis of career progression
        - improvement_areas: areas for resume enhancement
        - experience_level: inferred experience level
        - strengths: key strengths based on the resume
        """
        
        structured_output = await self.ai_client.generate_structured_output(
            prompt=prompt.format(content=content[:1000], basic_info=str(basic_info)),
            output_schema={
                "key_achievements": "array",
                "skills_assessment": "string",
                "career_progression": "string",
                "improvement_areas": "array",
                "experience_level": "string",
                "strengths": "array"
            }
        )
        
        return structured_output
    
    async def _extract_letter_insights(self, content: str, basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from letter"""
        prompt = """
        Analyze this letter and provide:
        1. Purpose of the letter
        2. Tone and style analysis
        3. Key points made
        4. Effectiveness assessment
        
        Basic Information already extracted:
        {basic_info}
        
        Content:
        {content}
        
        Provide a structured JSON response with the following fields:
        - purpose: inferred purpose of the letter
        - tone: overall tone of the letter
        - key_points: list of main points
        - effectiveness: assessment of effectiveness
        - letter_type: type of letter (recommendation, cover, etc.)
        """
        
        structured_output = await self.ai_client.generate_structured_output(
            prompt=prompt.format(content=content[:1000], basic_info=str(basic_info)),
            output_schema={
                "purpose": "string",
                "tone": "string",
                "key_points": "array",
                "effectiveness": "string",
                "letter_type": "string"
            }
        )
        
        return structured_output
    
    async def _extract_generic_insights(self, content: str, basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from generic document"""
        prompt = """
        Analyze this document and provide:
        1. Document type assessment
        2. Main purpose
        3. Key content summary
        4. Notable elements
        
        Content:
        {content}
        
        Provide a structured JSON response with the following fields:
        - likely_document_type: assessment of document type
        - purpose: inferred purpose of the document
        - content_summary: summary of key content
        - notable_elements: any notable or unusual elements
        """
        
        structured_output = await self.ai_client.generate_structured_output(
            prompt=prompt.format(content=content[:1000]),
            output_schema={
                "likely_document_type": "string",
                "purpose": "string",
                "content_summary": "string",
                "notable_elements": "array"
            }
        )
        
        return structured_output 