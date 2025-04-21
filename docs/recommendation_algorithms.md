# Recommendation Personalization Algorithms

This document provides technical details about the personalization algorithms used in the Profiler recommendation engine.

## Overview

The recommendation engine uses several personalization algorithms to generate tailored recommendations for each user. These algorithms analyze various data sources and apply different techniques to create the most relevant recommendations.

## Profile Analysis Algorithm

### Input Data
- User profile data (skills, experience, education, etc.)
- Profile completion metrics
- Section timestamps (when each profile section was last updated)

### Algorithm Steps
1. **Section Analysis**: Identify missing or incomplete sections
   ```python
   def analyze_profile_sections(profile):
       missing_sections = []
       for section in REQUIRED_SECTIONS:
           if section not in profile or not profile[section]:
               missing_sections.append(section)
       return missing_sections
   ```

2. **Content Quality Analysis**: Evaluate the quality and completeness of each section
   ```python
   def evaluate_section_quality(section_content):
       quality_score = 0
       if section_content:
           # Check content length
           quality_score += min(len(section_content) / 100, 0.5)
           
           # Check for specific keywords
           quality_score += 0.1 * count_industry_keywords(section_content)
           
           # Check for quantitative information
           quality_score += 0.2 * contains_quantitative_info(section_content)
       
       return min(quality_score, 1.0)
   ```

3. **Timestamp Analysis**: Identify outdated profile sections
   ```python
   def find_outdated_sections(profile, threshold_days=180):
       outdated_sections = []
       current_time = datetime.now()
       
       for section, content in profile.items():
           if section in profile.get("last_updated", {}):
               last_updated = profile["last_updated"][section]
               days_since_update = (current_time - last_updated).days
               
               if days_since_update > threshold_days:
                   outdated_sections.append(section)
       
       return outdated_sections
   ```

### Output
- List of profile recommendations with priority scores
- Action steps for each recommendation

## Peer Comparison Algorithm

### Input Data
- User's profile
- Profiles of peers with similar skills or industry
- Industry benchmarks and trends

### Algorithm Steps
1. **Find Similar Profiles**: Identify profiles with similar characteristics
   ```python
   def find_similar_profiles(user_profile, all_profiles, max_profiles=10):
       similarity_scores = []
       
       for profile_id, profile in all_profiles.items():
           if profile_id != user_profile["id"]:
               skill_similarity = compute_skill_similarity(
                   user_profile.get("skills", []),
                   profile.get("skills", [])
               )
               
               industry_similarity = compute_industry_similarity(
                   user_profile.get("industry", ""),
                   profile.get("industry", "")
               )
               
               experience_similarity = compute_experience_similarity(
                   user_profile.get("experience", []),
                   profile.get("experience", [])
               )
               
               # Weighted similarity
               total_similarity = (
                   0.5 * skill_similarity +
                   0.3 * industry_similarity +
                   0.2 * experience_similarity
               )
               
               similarity_scores.append((profile_id, total_similarity))
       
       # Get top similar profiles
       similarity_scores.sort(key=lambda x: x[1], reverse=True)
       top_similar_profiles = [all_profiles[profile_id] 
                              for profile_id, _ in similarity_scores[:max_profiles]]
       
       return top_similar_profiles
   ```

2. **Identify Differentiating Factors**: Find key differences between user's profile and peers
   ```python
   def identify_differences(user_profile, similar_profiles):
       # Initialize counters for different profile elements
       skill_counts = {}
       certification_counts = {}
       education_level_counts = {}
       
       # Analyze similar profiles
       for profile in similar_profiles:
           # Count skills
           for skill in profile.get("skills", []):
               skill_counts[skill] = skill_counts.get(skill, 0) + 1
           
           # Count certifications
           for cert in profile.get("certifications", []):
               cert_name = cert.get("name", "")
               if cert_name:
                   certification_counts[cert_name] = certification_counts.get(cert_name, 0) + 1
           
           # Count education levels
           for edu in profile.get("education", []):
               level = edu.get("degree", "")
               if level:
                   education_level_counts[level] = education_level_counts.get(level, 0) + 1
       
       # Find differences
       user_skills = set(user_profile.get("skills", []))
       user_certifications = set(cert.get("name", "") for cert in user_profile.get("certifications", []))
       user_education = set(edu.get("degree", "") for edu in user_profile.get("education", []))
       
       # Find common skills/certs/education not in user profile
       missing_skills = []
       missing_certifications = []
       missing_education = []
       
       # Calculate percentage of similar profiles with each element
       threshold_percentage = 0.3  # At least 30% of similar profiles have this element
       threshold_count = max(1, int(len(similar_profiles) * threshold_percentage))
       
       for skill, count in skill_counts.items():
           if skill not in user_skills and count >= threshold_count:
               missing_skills.append((skill, count / len(similar_profiles)))
       
       for cert, count in certification_counts.items():
           if cert not in user_certifications and count >= threshold_count:
               missing_certifications.append((cert, count / len(similar_profiles)))
       
       for level, count in education_level_counts.items():
           if level not in user_education and count >= threshold_count:
               missing_education.append((level, count / len(similar_profiles)))
       
       # Sort by prevalence
       missing_skills.sort(key=lambda x: x[1], reverse=True)
       missing_certifications.sort(key=lambda x: x[1], reverse=True)
       missing_education.sort(key=lambda x: x[1], reverse=True)
       
       return {
           "skills": missing_skills,
           "certifications": missing_certifications,
           "education": missing_education
       }
   ```

3. **Generate Peer-based Recommendations**: Create recommendations based on peer comparison
   ```python
   def generate_peer_recommendations(user_id, differences):
       recommendations = []
       
       # Skill recommendations
       for skill, prevalence in differences["skills"][:3]:  # Top 3 skills
           recommendations.append(
               Recommendation(
                   user_id=user_id,
                   title=f"Add {skill} to your skills",
                   description=f"{int(prevalence * 100)}% of professionals with similar profiles have this skill.",
                   category=RecommendationCategory.SKILL,
                   priority=min(0.4 + prevalence * 0.5, 0.9),  # Higher prevalence = higher priority
                   steps=[
                       f"Add {skill} to your profile",
                       f"Consider courses to develop your {skill} abilities",
                       "Update projects to demonstrate this skill"
                   ]
               )
           )
       
       # Certification recommendations
       for cert, prevalence in differences["certifications"][:2]:  # Top 2 certifications
           recommendations.append(
               Recommendation(
                   user_id=user_id,
                   title=f"Consider getting the {cert} certification",
                   description=f"{int(prevalence * 100)}% of professionals with similar profiles have this certification.",
                   category=RecommendationCategory.CERTIFICATION,
                   priority=min(0.5 + prevalence * 0.4, 0.85),
                   steps=[
                       f"Research the {cert} certification requirements",
                       "Find training resources",
                       "Create a study plan"
                   ]
               )
           )
       
       # Education recommendations
       for level, prevalence in differences["education"][:1]:  # Top education level
           recommendations.append(
               Recommendation(
                   user_id=user_id,
                   title=f"Consider pursuing a {level} degree",
                   description=f"{int(prevalence * 100)}% of professionals with similar profiles have this education level.",
                   category=RecommendationCategory.EDUCATION,
                   priority=min(0.3 + prevalence * 0.4, 0.7),
                   steps=[
                       f"Research {level} programs in your field",
                       "Evaluate online and in-person options",
                       "Consider time and financial commitments"
                   ]
               )
           )
       
       return recommendations
   ```

### Output
- Skill recommendations based on peer profiles
- Certification recommendations common among peers
- Education recommendations based on industry standards

## Document Analysis Algorithm

### Input Data
- User's uploaded documents (resume, CV, portfolio)
- Document metadata (creation date, last updated)
- Document content and structure

### Algorithm Steps
1. **Document Completeness Check**: Verify if required documents are present
   ```python
   def check_document_presence(user_documents):
       required_documents = ["resume", "cover_letter"]
       missing_documents = []
       
       user_document_types = [doc.get("type", "").lower() for doc in user_documents]
       
       for doc_type in required_documents:
           if doc_type not in user_document_types:
               missing_documents.append(doc_type)
       
       return missing_documents
   ```

2. **Content Quality Analysis**: Analyze document content for quality issues
   ```python
   def analyze_document_quality(document):
       issues = []
       
       # Check for document length
       if len(document.get("content", "")) < 300:
           issues.append({
               "type": "length",
               "description": "Your document is too short. Add more detail to make it comprehensive."
           })
       
       # Check for formatting consistency
       if not has_consistent_formatting(document.get("content", "")):
           issues.append({
               "type": "formatting",
               "description": "Your document has inconsistent formatting. Standardize headings and spacing."
           })
       
       # Check for action verbs in experience sections
       if not has_action_verbs(document.get("content", "")):
           issues.append({
               "type": "language",
               "description": "Use strong action verbs to describe your experience and achievements."
           })
       
       # Check for quantitative achievements
       if not has_quantitative_achievements(document.get("content", "")):
           issues.append({
               "type": "achievements",
               "description": "Add measurable achievements with numbers and percentages."
           })
       
       return issues
   ```

3. **Recency Check**: Identify outdated documents
   ```python
   def check_document_recency(document, threshold_days=90):
       if "last_updated" not in document:
           return True  # Can't determine if outdated
       
       last_updated = document["last_updated"]
       days_since_update = (datetime.now() - last_updated).days
       
       return days_since_update > threshold_days
   ```

### Output
- Document recommendations with specific issues to address
- Priority scores based on document importance and issue severity
- Step-by-step guidance for document improvement

## Q&A Analysis Algorithm

### Input Data
- User's Q&A history
- Q&A response quality metrics
- Unanswered questions

### Algorithm Steps
1. **Response Quality Analysis**: Evaluate the quality of user answers
   ```python
   async def evaluate_answer_quality(answer):
       # Factors that determine quality
       length_score = min(len(answer["content"]) / 150, 1.0)  # Reward longer answers up to a point
       
       # Check for specific details
       detail_score = 0.0
       if contains_specific_examples(answer["content"]):
           detail_score += 0.3
       if contains_quantitative_information(answer["content"]):
           detail_score += 0.3
       if contains_personal_experience(answer["content"]):
           detail_score += 0.4
       
       # Check for language quality
       language_score = calculate_language_quality(answer["content"])
       
       # Combined score with weights
       quality_score = (
           0.3 * length_score +
           0.4 * detail_score +
           0.3 * language_score
       )
       
       return min(quality_score, 1.0)  # Cap at 1.0
   ```

2. **Identify Low-Quality Answers**: Find answers that need improvement
   ```python
   async def identify_low_quality_answers(user_answers, threshold=0.6):
       low_quality_answers = []
       
       for answer in user_answers:
           quality = await evaluate_answer_quality(answer)
           if quality < threshold:
               low_quality_answers.append({
                   "answer_id": answer["id"],
                   "question_id": answer["question_id"],
                   "quality": quality,
                   "content": answer["content"]
               })
       
       return low_quality_answers
   ```

3. **Find Unanswered Questions**: Identify important questions the user hasn't answered
   ```python
   def find_unanswered_questions(user_id, all_questions, user_answers):
       answered_question_ids = {answer["question_id"] for answer in user_answers}
       
       unanswered_questions = []
       for question in all_questions:
           if question["id"] not in answered_question_ids:
               unanswered_questions.append(question)
       
       # Sort by importance
       unanswered_questions.sort(key=lambda q: q.get("importance", 0), reverse=True)
       
       return unanswered_questions
   ```

### Output
- Recommendations to improve answer quality
- Suggestions for unanswered important questions
- Examples of high-quality answers

## Integration and Filtering Algorithm

### Input Data
- Recommendations from all sources (profile, document, peer, Q&A)
- User's recommendation history
- User interaction data

### Algorithm Steps
1. **Combine Recommendations**: Gather recommendations from all sources
   ```python
   def combine_recommendations(profile_recs, peer_recs, document_recs, qa_recs):
       return profile_recs + peer_recs + document_recs + qa_recs
   ```

2. **Filter Duplicates and Similar Recommendations**: Remove redundant recommendations
   ```python
   def filter_duplicate_recommendations(new_recommendations, existing_recommendations):
       filtered_recommendations = []
       existing_titles = {rec.title for rec in existing_recommendations}
       
       for recommendation in new_recommendations:
           # Skip if the exact title already exists
           if recommendation.title in existing_titles:
               continue
               
           # Check for similar titles
           similar_exists = False
           for existing_title in existing_titles:
               if (recommendation.title in existing_title or 
                   existing_title in recommendation.title) and \
                  recommendation.category == next(
                      (rec.category for rec in existing_recommendations if rec.title == existing_title), 
                      None
                  ):
                   similar_exists = True
                   break
                   
           if not similar_exists:
               filtered_recommendations.append(recommendation)
               existing_titles.add(recommendation.title)  # Update for subsequent checks
               
       return filtered_recommendations
   ```

3. **Prioritize Recommendations**: Adjust priorities based on multiple factors
   ```python
   def prioritize_recommendations(recommendations, user_history):
       # Calculate timing factor (recommendations not shown recently get higher priority)
       now = datetime.now()
       
       for rec in recommendations:
           # Check if similar recommendations were recently completed
           similar_completed = [
               h for h in user_history 
               if h.category == rec.category and h.status == "completed" and
               (now - h.completed_at).days < 30
           ]
           
           # Reduce priority if similar recommendations were recently completed
           if similar_completed:
               rec.priority = max(rec.priority - 0.2, 0.1)
           
           # Boost priority for recommendations that complement recent activity
           if should_boost_priority(rec, user_history):
               rec.priority = min(rec.priority + 0.15, 1.0)
       
       # Sort by adjusted priority
       return sorted(recommendations, key=lambda r: r.priority, reverse=True)
   ```

4. **Limit Recommendations**: Prevent overwhelming the user
   ```python
   def limit_recommendations(recommendations, max_active=5):
       # Group by category
       by_category = {}
       for rec in recommendations:
           if rec.category not in by_category:
               by_category[rec.category] = []
           by_category[rec.category].append(rec)
       
       # Ensure diversity by taking top recommendations from each category
       limited_recommendations = []
       categories = list(by_category.keys())
       
       while len(limited_recommendations) < max_active and categories:
           for category in list(categories):  # Use a copy to avoid modification during iteration
               if by_category[category]:
                   limited_recommendations.append(by_category[category].pop(0))
                   if len(limited_recommendations) >= max_active:
                       break
               else:
                   categories.remove(category)
       
       return limited_recommendations
   ```

### Output
- Filtered, prioritized list of recommendations
- Diverse set of recommendations across different categories
- Maximum number of active recommendations to prevent overwhelming the user

## Implementation Details

The algorithms above are implemented in the `RecommendationService` class, which orchestrates the overall recommendation generation process:

```python
async def generate_recommendations_for_user(self, user_id: str) -> List[Recommendation]:
    """Generate recommendations for a user based on their profile, Q&A history, and documents.
    
    Args:
        user_id: The ID of the user to generate recommendations for.
        
    Returns:
        A list of recommendations for the user.
    """
    # Get existing active recommendations
    existing_recommendations = await self.get_recommendations_for_user(user_id, status="active")
    
    # Get user profile
    profile = await self.profile_service.get_profile(user_id)
    
    # Generate profile-based recommendations
    recommendations = []
    if profile:
        profile_recommendations = await self._generate_profile_recommendations(profile)
        recommendations.extend(profile_recommendations)
        
        # Generate peer comparison recommendations
        peer_recommendations = await self._generate_peer_comparison_recommendations(profile)
        recommendations.extend(peer_recommendations)
    
    # Generate document-based recommendations
    document_recommendations = await self._generate_document_recommendations(user_id)
    recommendations.extend(document_recommendations)
    
    # Generate Q&A-based recommendations
    qa_recommendations = await self._generate_qa_recommendations(user_id)
    recommendations.extend(qa_recommendations)
    
    # Filter out duplicates or recommendations similar to existing ones
    unique_recommendations = self._filter_duplicate_recommendations(recommendations, existing_recommendations)
    
    # Save the new recommendations
    saved_recommendations = []
    for recommendation in unique_recommendations:
        saved = await self.recommendation_repository.save_recommendation(recommendation)
        if saved:
            saved_recommendations.append(saved)
            
            # Send notification for the new recommendation
            await self.notification_service.create_recommendation_notification(
                user_id=user_id,
                recommendation_id=saved.id,
                title=saved.title,
                description=saved.description
            )
    
    return saved_recommendations
```

## Future Algorithm Enhancements

Future versions of the recommendation engine will include:

1. **Machine Learning Models**: Train models on user behavior to predict which recommendations are most likely to be followed
2. **Natural Language Processing**: Use NLP to better analyze document content and Q&A responses
3. **Temporal Analysis**: Adjust recommendations based on seasonal factors and industry trends
4. **Collaborative Filtering**: Use techniques similar to recommendation systems in e-commerce
5. **A/B Testing Framework**: Continuously optimize recommendation algorithms based on user engagement metrics 