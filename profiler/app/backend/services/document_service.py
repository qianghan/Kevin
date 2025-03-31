from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import re
from datetime import datetime

from ..core.deepseek.r1 import DeepSeekR1
from ..core.config import settings

class DocumentAnalysis(BaseModel):
    """Model for document analysis results"""
    content_type: str = Field(..., description="Type of document")
    extracted_info: Dict[str, Any] = Field(..., description="Extracted information")
    confidence: float = Field(..., description="Confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class DocumentService:
    """Service for analyzing documents and extracting information"""
    
    def __init__(self):
        # Initialize DeepSeek client for batch processing
        self.llm = DeepSeekR1(
            api_key=settings.DEEPSEEK_API_KEY,
            model="deepseek-ai/deepseek-r1"
        )
        
        # Define document type patterns
        self.document_patterns = {
            "transcript": {
                "grade_pattern": r"([A-Z][+-]?)\s*(\d{1,2}(?:\.\d{1,2})?)",
                "course_pattern": r"([A-Z]{2,4}\s*\d{3,4}[A-Z]?)\s*([^0-9]+)",
                "term_pattern": r"(Fall|Spring|Summer)\s*(\d{4})"
            },
            "essay": {
                "word_count_pattern": r"\b\w+\b",
                "paragraph_pattern": r"\n\s*\n"
            },
            "resume": {
                "section_pattern": r"^([A-Z][a-z\s]+):",
                "date_pattern": r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4}"
            }
        }
    
    async def analyze(
        self,
        content: str,
        document_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentAnalysis:
        """Analyze document content and extract information"""
        try:
            # Validate document type
            if document_type not in self.document_patterns:
                raise ValueError(f"Unsupported document type: {document_type}")
            
            # Extract basic information
            extracted_info = await self._extract_basic_info(
                content,
                document_type
            )
            
            # Perform deep analysis
            deep_analysis = await self._perform_deep_analysis(
                content,
                document_type,
                extracted_info
            )
            
            # Merge results
            final_info = {
                **extracted_info,
                **deep_analysis
            }
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                final_info,
                document_type
            )
            
            # Create analysis result
            return DocumentAnalysis(
                content_type=document_type,
                extracted_info=final_info,
                confidence=confidence,
                metadata={
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "document_length": len(content),
                    **(metadata or {})
                }
            )
            
        except Exception as e:
            print(f"Error analyzing document: {str(e)}")
            raise
    
    async def _extract_basic_info(
        self,
        content: str,
        document_type: str
    ) -> Dict[str, Any]:
        """Extract basic information using patterns"""
        patterns = self.document_patterns[document_type]
        info = {}
        
        if document_type == "transcript":
            # Extract grades
            grades = re.finditer(patterns["grade_pattern"], content)
            info["grades"] = [
                {"grade": m.group(1), "score": float(m.group(2))}
                for m in grades
            ]
            
            # Extract courses
            courses = re.finditer(patterns["course_pattern"], content)
            info["courses"] = [
                {"code": m.group(1), "name": m.group(2).strip()}
                for m in courses
            ]
            
            # Extract terms
            terms = re.finditer(patterns["term_pattern"], content)
            info["terms"] = [
                {"term": m.group(1), "year": int(m.group(2))}
                for m in terms
            ]
        
        elif document_type == "essay":
            # Count words
            words = re.findall(patterns["word_count_pattern"], content)
            info["word_count"] = len(words)
            
            # Count paragraphs
            paragraphs = re.split(patterns["paragraph_pattern"], content)
            info["paragraph_count"] = len(paragraphs)
            
            # Extract key phrases
            info["key_phrases"] = await self._extract_key_phrases(content)
        
        elif document_type == "resume":
            # Extract sections
            sections = re.finditer(patterns["section_pattern"], content, re.MULTILINE)
            info["sections"] = [m.group(1).strip() for m in sections]
            
            # Extract dates
            dates = re.finditer(patterns["date_pattern"], content)
            info["dates"] = [m.group(0) for m in dates]
            
            # Extract skills
            info["skills"] = await self._extract_skills(content)
        
        return info
    
    async def _perform_deep_analysis(
        self,
        content: str,
        document_type: str,
        basic_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform deep analysis using LLM"""
        try:
            # Prepare analysis prompt
            prompt = self._create_analysis_prompt(
                content,
                document_type,
                basic_info
            )
            
            # Perform analysis
            result = await self.llm.analyze(
                text=content,
                task=f"analyze_{document_type}",
                context={"basic_info": basic_info}
            )
            
            return result["analysis"]
            
        except Exception as e:
            print(f"Error in deep analysis: {str(e)}")
            return {}
    
    async def _extract_key_phrases(self, content: str) -> List[str]:
        """Extract key phrases from text"""
        try:
            result = await self.llm.analyze(
                text=content,
                task="extract_key_phrases"
            )
            return result["analysis"].get("key_phrases", [])
        except Exception:
            return []
    
    async def _extract_skills(self, content: str) -> List[str]:
        """Extract skills from resume"""
        try:
            result = await self.llm.analyze(
                text=content,
                task="extract_skills"
            )
            return result["analysis"].get("skills", [])
        except Exception:
            return []
    
    def _create_analysis_prompt(
        self,
        content: str,
        document_type: str,
        basic_info: Dict[str, Any]
    ) -> str:
        """Create analysis prompt based on document type"""
        prompts = {
            "transcript": """Analyze this academic transcript and provide:
            1. Overall academic performance
            2. Course selection patterns
            3. Areas of strength and improvement
            4. Academic trends over time
            
            Basic Information:
            {basic_info}
            
            Content:
            {content}""",
            
            "essay": """Analyze this essay and provide:
            1. Main themes and arguments
            2. Writing style and tone
            3. Strengths and areas for improvement
            4. Personal insights and experiences
            
            Basic Information:
            {basic_info}
            
            Content:
            {content}""",
            
            "resume": """Analyze this resume and provide:
            1. Key achievements and experiences
            2. Skills and qualifications
            3. Career progression
            4. Areas for enhancement
            
            Basic Information:
            {basic_info}
            
            Content:
            {content}"""
        }
        
        return prompts.get(
            document_type,
            "Analyze this document and provide key insights."
        ).format(
            content=content,
            basic_info=basic_info
        )
    
    def _calculate_confidence(
        self,
        info: Dict[str, Any],
        document_type: str
    ) -> float:
        """Calculate confidence score for analysis"""
        # This would use various heuristics based on document type
        if document_type == "transcript":
            # Check completeness of grade and course information
            grades = info.get("grades", [])
            courses = info.get("courses", [])
            return min(1.0, (len(grades) + len(courses)) / 20)
        
        elif document_type == "essay":
            # Check word count and paragraph structure
            word_count = info.get("word_count", 0)
            paragraph_count = info.get("paragraph_count", 0)
            return min(1.0, (word_count / 500 + paragraph_count / 5) / 2)
        
        elif document_type == "resume":
            # Check completeness of sections and skills
            sections = info.get("sections", [])
            skills = info.get("skills", [])
            return min(1.0, (len(sections) + len(skills)) / 15)
        
        return 0.5  # Default confidence 