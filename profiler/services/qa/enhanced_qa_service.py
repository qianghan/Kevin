from typing import List, Dict, Any, Optional, Union, BinaryIO
import uuid
import json
import os
from datetime import datetime
import re

from profiler.services.qa.qa_service import QAService


class EnhancedQAService(QAService):
    """
    Enhanced implementation of the QA service with advanced features.
    Extends the base QAService with improved question generation, answer processing,
    multimedia support, and analytics capabilities.
    """
    
    def __init__(self, qa_repository, profile_repository=None, question_bank_path=None):
        """
        Initialize the enhanced QA service.
        
        Args:
            qa_repository: The repository for Q&A data
            profile_repository: Optional repository for profile data
            question_bank_path: Optional path to question bank file
        """
        super().__init__(qa_repository)
        self.profile_repository = profile_repository
        self.question_bank = self._load_question_bank(question_bank_path)
        self.answer_quality_thresholds = {
            "excellent": 0.9,
            "good": 0.7,
            "adequate": 0.5,
            "poor": 0.3
        }
        
    def _load_question_bank(self, path: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load the question bank from a file or use default questions.
        
        Args:
            path: Path to the question bank file
            
        Returns:
            Dictionary mapping categories to lists of questions
        """
        default_question_bank = {
            "professional": [
                {"text": "What is your current job title?", "importance": 0.9},
                {"text": "How many years of experience do you have in your field?", "importance": 0.8},
                {"text": "What are your primary responsibilities in your current role?", "importance": 0.9}
            ],
            "education": [
                {"text": "What is your highest level of education?", "importance": 0.9},
                {"text": "What was your major or field of study?", "importance": 0.8},
                {"text": "Have you completed any additional certifications?", "importance": 0.7}
            ],
            "skills": [
                {"text": "What are your top technical skills?", "importance": 0.9},
                {"text": "What soft skills do you consider as your strengths?", "importance": 0.8},
                {"text": "Rate your proficiency in the technologies you use most often.", "importance": 0.7}
            ],
            "projects": [
                {"text": "What was the most significant project you've worked on?", "importance": 0.8},
                {"text": "What was your role in that project?", "importance": 0.7},
                {"text": "What technologies or methodologies did you use?", "importance": 0.7}
            ]
        }
        
        if path and os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return default_question_bank
        return default_question_bank
    
    async def get_profile_data(self, profile_id: str) -> Dict[str, Any]:
        """
        Get profile data from the profile repository.
        
        Args:
            profile_id: The ID of the profile
            
        Returns:
            The profile data
            
        Raises:
            ValueError: If profile repository is not available
        """
        if self.profile_repository is None:
            raise ValueError("Profile repository is not available")
        
        profile = await self.profile_repository.get_profile(profile_id)
        return profile.to_dict() if hasattr(profile, 'to_dict') else profile
    
    def generate_questions(self, profile_data: Dict[str, Any], categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Generate questions based on a user's profile.
        
        Args:
            profile_data: The user's profile data
            categories: Optional list of categories to focus on
            
        Returns:
            A list of question objects
        """
        # First try to get questions from the repository
        profile_id = profile_data.get('id')
        stored_questions = self.repository.get_questions_for_profile(profile_id)
        
        # If we have enough questions, return them
        if len(stored_questions) >= 5:
            return stored_questions
        
        # Otherwise, generate new questions based on profile data and question bank
        if categories is None:
            # Analyze profile to determine which categories need more information
            categories = self._analyze_profile_completion(profile_data)
        
        generated_questions = []
        
        for category in categories:
            # Get questions from the question bank for this category
            bank_questions = self.question_bank.get(category, [])
            
            # Customize questions based on profile data
            for question_template in bank_questions:
                question_text = self._customize_question(question_template["text"], profile_data)
                
                # Create a question object
                question = {
                    "id": str(uuid.uuid4()),
                    "text": question_text,
                    "category": category,
                    "importance": question_template.get("importance", 0.5),
                    "generated_at": datetime.now().isoformat(),
                    "profile_id": profile_id,
                    "follow_up_questions": []
                }
                
                # Save the question to the repository
                question_id = self.repository.save_question(question)
                question["id"] = question_id
                
                generated_questions.append(question)
        
        # Combine stored and generated questions
        all_questions = stored_questions + generated_questions
        
        # Sort by importance
        all_questions.sort(key=lambda q: q.get("importance", 0), reverse=True)
        
        return all_questions
    
    def _analyze_profile_completion(self, profile_data: Dict[str, Any]) -> List[str]:
        """
        Analyze profile data to determine which categories need more information.
        
        Args:
            profile_data: The user's profile data
            
        Returns:
            List of categories that need more information
        """
        categories_to_focus = []
        
        # Check professional info
        if not profile_data.get("professional_info") or len(profile_data.get("professional_info", {})) < 3:
            categories_to_focus.append("professional")
        
        # Check education
        if not profile_data.get("education") or len(profile_data.get("education", [])) < 1:
            categories_to_focus.append("education")
        
        # Check skills
        if not profile_data.get("skills") or len(profile_data.get("skills", [])) < 3:
            categories_to_focus.append("skills")
        
        # Check projects
        if not profile_data.get("projects") or len(profile_data.get("projects", [])) < 1:
            categories_to_focus.append("projects")
        
        # If all categories have sufficient information, focus on skills (always good to have more)
        if not categories_to_focus:
            categories_to_focus = ["skills"]
        
        return categories_to_focus
    
    def _customize_question(self, question_text: str, profile_data: Dict[str, Any]) -> str:
        """
        Customize a question based on profile data.
        
        Args:
            question_text: The question template text
            profile_data: The user's profile data
            
        Returns:
            Customized question text
        """
        # Replace placeholders with profile data
        customized = question_text
        
        # Replace {name} with user's name
        if "{name}" in customized and "name" in profile_data:
            customized = customized.replace("{name}", profile_data["name"])
        
        # Replace {current_job} with user's current job title
        if "{current_job}" in customized and "professional_info" in profile_data:
            prof_info = profile_data.get("professional_info", {})
            current_job = prof_info.get("title", "your current job")
            customized = customized.replace("{current_job}", current_job)
        
        # Replace {company} with user's company
        if "{company}" in customized and "professional_info" in profile_data:
            prof_info = profile_data.get("professional_info", {})
            company = prof_info.get("company", "your company")
            customized = customized.replace("{company}", company)
            
        # Remove any remaining placeholders
        customized = re.sub(r"\{[^}]+\}", "", customized)
        
        return customized
    
    def process_answer(self, question_id: str, answer: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a user's answer to a question.
        
        Args:
            question_id: The ID of the question being answered
            answer: The user's answer text or multimedia answer
            
        Returns:
            The processed answer object
        """
        # Handle different answer types
        if isinstance(answer, str):
            # Text answer
            processed_answer = {
                "question_id": question_id,
                "answer_text": answer,
                "processed": True,
                "answer_type": "text",
                "processed_at": datetime.now().isoformat(),
                "quality_score": self._calculate_answer_quality(question_id, answer)
            }
        else:
            # Multimedia answer
            processed_answer = {
                "question_id": question_id,
                "answer_text": answer.get("text", ""),
                "media_type": answer.get("media_type", "unknown"),
                "media_url": answer.get("media_url", ""),
                "processed": True,
                "answer_type": "multimedia",
                "processed_at": datetime.now().isoformat(),
                "quality_score": self._calculate_answer_quality(question_id, answer.get("text", ""))
            }
        
        # Extract key information from the answer
        extracted_info = self._extract_information(question_id, processed_answer)
        processed_answer["extracted_information"] = extracted_info
        
        # Save the answer
        self.repository.save_answer(question_id, processed_answer)
        
        # Generate follow-up questions based on this answer
        question = self.repository.get_question(question_id)
        follow_up_questions = self._generate_follow_up_questions(question, processed_answer)
        
        # Update the question with follow-up question IDs
        question["follow_up_questions"] = [q["id"] for q in follow_up_questions]
        self.repository.save_question(question)
        
        return processed_answer
    
    def _calculate_answer_quality(self, question_id: str, answer_text: str) -> float:
        """Calculate the quality score for an answer."""
        # Simple implementation
        if len(answer_text) < 20:
            return 0.3  # Low quality for very short answers
        elif len(answer_text) > 200:
            return 0.8  # Higher quality for detailed answers
        else:
            return 0.5  # Medium quality for average length answers
    
    def evaluate_answer_quality(self, question, answer_text):
        """Evaluate the quality of an answer to a question.
        
        This is a convenience method that wraps _calculate_answer_quality
        and provides a more detailed quality assessment.
        """
        quality_score = self._calculate_answer_quality(question["id"], answer_text)
        
        # Extract information from the answer
        extracted_info = self._extract_key_information(question, answer_text)
        
        # Generate feedback for low-quality answers
        feedback = []
        if quality_score < 0.5:
            feedback = self._provide_answer_feedback(question, answer_text, quality_score)
        
        return {
            "quality_score": quality_score,
            "extracted_information": extracted_info,
            "feedback": feedback
        }
    
    def _extract_key_information(self, question, answer_text):
        """Extract key information from an answer based on the question type.
        
        This is a wrapper around _extract_information to match the expected interface.
        """
        # Extract information based on question category
        result = {}
        
        # Extract skills for skills questions
        if question.get("category") == "skills":
            skill_objects = self._extract_skills(answer_text)
            if skill_objects:
                # Extract just the skill names for the test
                skill_names = [skill["name"] for skill in skill_objects]
                result["skills"] = skill_names
            
        # Extract experience information for professional questions
        if question.get("category") == "professional":
            # Extract job titles
            job_titles = self._extract_job_titles(answer_text)
            if job_titles:
                result["job_titles"] = job_titles
            
            # Extract years of experience
            years = self._extract_years_of_experience(answer_text)
            if years:
                result["years_of_experience"] = years
        
        # Extract education information for education questions
        if question.get("category") == "education":
            # Extract degrees
            degrees = self._extract_degrees(answer_text)
            if degrees:
                result["degrees"] = degrees
            
            # Extract institutions
            institutions = self._extract_institutions(answer_text)
            if institutions:
                result["institutions"] = institutions
        
        # Always try to extract technologies mentioned
        technologies = self._extract_technologies(answer_text)
        if technologies:
            result["technologies"] = technologies
        
        return result
    
    def _extract_technologies(self, text: str) -> List[str]:
        """Extract technologies mentioned in text."""
        technologies = []
        tech_keywords = [
            "Python", "JavaScript", "Java", "C++", "C#", "Ruby", "Go", "Rust",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
            "React", "Angular", "Vue", "Node.js", "Django", "Flask", "Spring",
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "GitHub", "Linux",
            "TensorFlow", "PyTorch", "scikit-learn", "pandas", "numpy"
        ]
        
        for tech in tech_keywords:
            if tech in text:
                technologies.append(tech)
        
        return technologies
    
    def _provide_answer_feedback(self, question, answer_text, quality_score=None):
        """Generate feedback for improving an answer.
        
        Args:
            question: The question dictionary
            answer_text: The text of the answer
            quality_score: Optional pre-calculated quality score
            
        Returns:
            List of feedback suggestions
        """
        feedback = []
        
        # Calculate quality if not provided
        if quality_score is None:
            quality_score = self._calculate_answer_quality(question["id"], answer_text)
        
        # Generate specific feedback based on quality
        if quality_score < 0.4:
            feedback.append("Your answer is quite brief. Consider adding more details.")
            feedback.append("Try to include specific examples from your experience.")
            
        elif quality_score < 0.7:
            feedback.append("Consider expanding on your key points to add more detail.")
            feedback.append("Adding specific details will make your answer more compelling.")
            
            # Add category-specific feedback
            if question.get("category") == "skills":
                feedback.append("Mention specific technologies or tools you've used.")
            elif question.get("category") == "professional":
                feedback.append("Include measurable achievements or results.")
                
        # Check for inclusion of key terms
        key_terms = {
            "skills": ["years of experience", "proficiency", "projects"],
            "education": ["degree", "university", "courses", "skills learned"],
            "professional": ["responsibilities", "achievements", "technologies used"]
        }
        
        category = question.get("category", "")
        if category in key_terms:
            for term in key_terms[category]:
                if term.lower() not in answer_text.lower():
                    feedback.append(f"Consider including information about your {term}.")
                    break
                
        return feedback
    
    def _extract_information(self, question_id: str, answer: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured information from an answer."""
        # Get the question
        question = self.repository.get_question(question_id)
        category = question.get("category", "")
        answer_text = answer.get("answer_text", "")
        
        # Extract information based on category
        extracted = {}
        
        if category == "professional":
            # Extract job titles, years of experience, etc.
            job_titles = self._extract_job_titles(answer_text)
            years_of_experience = self._extract_years_of_experience(answer_text)
            
            if job_titles:
                extracted["job_titles"] = job_titles
            if years_of_experience is not None:
                extracted["years_of_experience"] = years_of_experience
                
        elif category == "education":
            # Extract degrees, institutions, etc.
            degrees = self._extract_degrees(answer_text)
            institutions = self._extract_institutions(answer_text)
            
            if degrees:
                extracted["degrees"] = degrees
            if institutions:
                extracted["institutions"] = institutions
                
        elif category == "skills":
            # Extract skills and proficiency levels
            skills = self._extract_skills(answer_text)
            if skills:
                extracted["skills"] = skills
        
        # More categories and extraction methods would be added here
        
        return extracted
    
    def _extract_job_titles(self, text: str) -> List[str]:
        """Extract job titles from text."""
        # Simple implementation for demonstration
        common_titles = ["developer", "engineer", "manager", "director", "analyst", "designer", "consultant"]
        titles = []
        
        for title in common_titles:
            if title in text.lower():
                titles.append(title)
                
        return titles
    
    def _extract_years_of_experience(self, text: str) -> Optional[int]:
        """Extract years of experience from text."""
        # Simple regex pattern to find numbers preceded by year-related words
        matches = re.findall(r"(\d+)[ -]*(years?|yrs)", text.lower())
        if matches:
            return int(matches[0][0])
        return None
    
    def _extract_degrees(self, text: str) -> List[str]:
        """Extract degrees from text."""
        common_degrees = ["bachelor", "master", "phd", "doctorate", "bs", "ba", "ms", "ma", "mba"]
        degrees = []
        
        for degree in common_degrees:
            if degree in text.lower():
                degrees.append(degree)
                
        return degrees
    
    def _extract_institutions(self, text: str) -> List[str]:
        """Extract educational institutions from text."""
        # This would use a more sophisticated entity recognition in a real implementation
        # Simple keyword check for demonstration
        common_keywords = ["university", "college", "institute", "school"]
        institutions = []
        
        for keyword in common_keywords:
            if keyword in text.lower():
                # Try to get the full institution name
                pattern = re.compile(r"([A-Z][a-z]+ )+" + keyword, re.IGNORECASE)
                matches = pattern.findall(text)
                if matches:
                    institutions.extend(matches)
                else:
                    institutions.append(keyword)
                
        return institutions
    
    def _extract_skills(self, text: str) -> List[Dict[str, Any]]:
        """Extract skills from text.
        
        Args:
            text: The text to extract skills from
            
        Returns:
            List of extracted skills with name and proficiency
        """
        skills = []
        
        # Extract skills based on known programming languages, frameworks, etc.
        skill_keywords = [
            "Python", "JavaScript", "Java", "C++", "C#", "Ruby", "Go", "Rust",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
            "React", "Angular", "Vue", "Node.js", "Django", "Flask", "Spring",
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "GitHub", "Linux",
            "TensorFlow", "PyTorch", "scikit-learn", "pandas", "numpy"
        ]
        
        # Get lowercase versions for comparison
        skill_keywords_lower = {s.lower(): s for s in skill_keywords}
        
        # Common skill phrases to look for
        skill_phrases = [
            r'\b(experienced|proficient|skilled|expert|knowledge)\s+in\s+([A-Za-z+#]+)',
            r'\b(used|worked with|developed with|programmed in)\s+([A-Za-z+#]+)',
            r'\b([A-Za-z+#]+)\s+(developer|programmer|engineer)',
        ]
        
        # Extract directly mentioned skills
        for skill in skill_keywords:
            if skill in text:
                skills.append(skill)
        
        # Process extracted skills into structured format
        result = []
        for skill in skills:
            result.append({
                "name": skill,
                "proficiency": 0.7 if "expert" in text.lower() or "advanced" in text.lower() else 0.5
            })
        
        return result
    
    def _generate_follow_up_questions(self, question: Dict[str, Any], answer: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate follow-up questions based on a question and its answer.
        
        Args:
            question: The original question
            answer: The processed answer
            
        Returns:
            List of follow-up question objects
        """
        follow_ups = []
        category = question.get("category", "")
        answer_text = answer.get("answer_text", "")
        extracted_info = answer.get("extracted_information", {})
        
        # Generate follow-ups based on category and extracted information
        if category == "professional":
            # Follow up on job titles
            job_titles = extracted_info.get("job_titles", [])
            if job_titles and len(job_titles) > 0:
                follow_up = {
                    "id": str(uuid.uuid4()),
                    "text": f"What were your main responsibilities as a {job_titles[0]}?",
                    "category": "professional",
                    "importance": 0.8,
                    "generated_at": datetime.now().isoformat(),
                    "profile_id": question.get("profile_id"),
                    "parent_question_id": question.get("id"),
                    "follow_up_questions": []
                }
                # Save the question
                follow_up["id"] = self.repository.save_question(follow_up)
                follow_ups.append(follow_up)
            
            # Follow up on years of experience
            years_of_experience = extracted_info.get("years_of_experience")
            if years_of_experience is not None:
                follow_up = {
                    "id": str(uuid.uuid4()),
                    "text": f"How has your role evolved over your {years_of_experience} years in the field?",
                    "category": "professional",
                    "importance": 0.7,
                    "generated_at": datetime.now().isoformat(),
                    "profile_id": question.get("profile_id"),
                    "parent_question_id": question.get("id"),
                    "follow_up_questions": []
                }
                # Save the question
                follow_up["id"] = self.repository.save_question(follow_up)
                follow_ups.append(follow_up)
                
        elif category == "education":
            # Follow up on degrees
            degrees = extracted_info.get("degrees", [])
            if degrees and len(degrees) > 0:
                follow_up = {
                    "id": str(uuid.uuid4()),
                    "text": f"How has your {degrees[0]} degree helped you in your career?",
                    "category": "education",
                    "importance": 0.7,
                    "generated_at": datetime.now().isoformat(),
                    "profile_id": question.get("profile_id"),
                    "parent_question_id": question.get("id"),
                    "follow_up_questions": []
                }
                # Save the question
                follow_up["id"] = self.repository.save_question(follow_up)
                follow_ups.append(follow_up)
                
        elif category == "skills":
            # Follow up on skills
            skills = extracted_info.get("skills", [])
            if skills and len(skills) > 0:
                skill_name = skills[0].get("name", "this skill")
                follow_up = {
                    "id": str(uuid.uuid4()),
                    "text": f"Can you describe a project where you used {skill_name}?",
                    "category": "skills",
                    "importance": 0.8,
                    "generated_at": datetime.now().isoformat(),
                    "profile_id": question.get("profile_id"),
                    "parent_question_id": question.get("id"),
                    "follow_up_questions": []
                }
                # Save the question
                follow_up["id"] = self.repository.save_question(follow_up)
                follow_ups.append(follow_up)
        
        # Add generic follow-ups based on answer quality
        quality_score = answer.get("quality_score", 0)
        if quality_score < 0.5 and len(answer_text) < 50:
            # If the answer is short and low quality, ask for more details
            follow_up = {
                "id": str(uuid.uuid4()),
                "text": "Could you elaborate more on your previous answer?",
                "category": category,
                "importance": 0.6,
                "generated_at": datetime.now().isoformat(),
                "profile_id": question.get("profile_id"),
                "parent_question_id": question.get("id"),
                "follow_up_questions": []
            }
            # Save the question
            follow_up["id"] = self.repository.save_question(follow_up)
            follow_ups.append(follow_up)
        
        return follow_ups
    
    def process_multimedia_answer(self, question_id: str, text: str, media_type: str, file_data: BinaryIO) -> Dict[str, Any]:
        """
        Process a multimedia answer (image, audio, video).
        
        Args:
            question_id: The ID of the question
            text: Accompanying text for the media
            media_type: Type of media (image, audio, video)
            file_data: Binary file data
            
        Returns:
            Processed answer object
        """
        # Save the file data and get a URL
        media_url = self._save_media_file(file_data, media_type)
        
        # Process the answer
        answer = {
            "text": text,
            "media_type": media_type,
            "media_url": media_url
        }
        
        return self.process_answer(question_id, answer)
    
    def _save_media_file(self, file_data: BinaryIO, media_type: str) -> str:
        """
        Save media file and return a URL.
        
        Args:
            file_data: Binary file data
            media_type: Type of media (image, audio, video)
            
        Returns:
            URL to the saved media file
        """
        # In a real implementation, this would save to a CDN or file storage
        # For demonstration, we'll return a placeholder URL
        return f"/media/{str(uuid.uuid4())}.{media_type}"
    
    def batch_process_answers(self, answers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple answers in batch.
        
        Args:
            answers: List of answer objects with question_id and answer_text
            
        Returns:
            List of processed answer objects
        """
        processed_answers = []
        
        for answer_data in answers:
            question_id = answer_data.get("question_id")
            answer = answer_data.get("answer_text") or answer_data  # Handle both formats
            
            if question_id:
                processed_answer = self.process_answer(question_id, answer)
                processed_answers.append(processed_answer)
        
        return processed_answers
    
    def export_qa_session(self, profile_id: str) -> Dict[str, Any]:
        """
        Export a Q&A session for a profile.
        
        Args:
            profile_id: The ID of the profile
            
        Returns:
            Q&A session data
        """
        # Get all questions and answers for the profile
        history = self.get_question_history(profile_id)
        
        # Structure the data
        qa_session = {
            "profile_id": profile_id,
            "exported_at": datetime.now().isoformat(),
            "questions_count": len(history),
            "answered_count": sum(1 for q in history if q.get("answer")),
            "history": history,
            "analytics": self.get_profile_qa_analytics(profile_id)
        }
        
        return qa_session
    
    def get_profile_qa_analytics(self, profile_id: str) -> Dict[str, Any]:
        """
        Get analytics for a profile's Q&A session.
        
        Args:
            profile_id: The ID of the profile
            
        Returns:
            Analytics data
        """
        history = self.get_question_history(profile_id)
        
        # Count questions by category
        categories = {}
        answer_quality = []
        
        for item in history:
            category = item.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
            
            answer = item.get("answer")
            if answer:
                quality_score = answer.get("quality_score", 0)
                answer_quality.append(quality_score)
        
        # Calculate statistics
        avg_quality = sum(answer_quality) / len(answer_quality) if answer_quality else 0
        
        return {
            "total_questions": len(history),
            "answered_questions": len(answer_quality),
            "completion_rate": len(answer_quality) / len(history) if history else 0,
            "categories": categories,
            "average_answer_quality": avg_quality,
            "excellent_answers": sum(1 for q in answer_quality if q >= self.answer_quality_thresholds["excellent"]),
            "good_answers": sum(1 for q in answer_quality if self.answer_quality_thresholds["good"] <= q < self.answer_quality_thresholds["excellent"]),
            "adequate_answers": sum(1 for q in answer_quality if self.answer_quality_thresholds["adequate"] <= q < self.answer_quality_thresholds["good"]),
            "poor_answers": sum(1 for q in answer_quality if q < self.answer_quality_thresholds["adequate"])
        } 