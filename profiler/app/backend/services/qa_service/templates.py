"""
Prompt templates for the QA service.

This module defines templates for prompts used by the QA service components.
"""

# Template for generating questions based on profile data
QUESTION_GENERATION_PROMPT = """
Generate questions to help build a student profile based on the following information:

Profile Data:
{profile_data}

Categories to focus on:
{categories}

Please generate {count} relevant questions that will help gather more information 
about the student's profile. Each question should:

1. Be specific and clear
2. Help gather meaningful information
3. Be tailored to the student's background as shown in the profile data
4. Include potential follow-up questions where appropriate

Return the questions in the following structured format:
[
  {{
    "category": "category_name",  // one of the categories from the list above
    "question_text": "The question to ask",
    "expected_response_type": "text/number/date/list/boolean", // expected type of response
    "required": true/false,  // whether this question is required
    "follow_up_questions": ["potential follow-up 1", "potential follow-up 2"]  // potential follow-ups
  }},
  // more questions...
]

Focus on quality over quantity. Make sure each question is relevant and helpful.
"""

# Template for generating follow-up questions
FOLLOW_UP_PROMPT = """
Based on the following question and answer, generate follow-up questions 
to gather more detailed information:

Original Question: {original_question}

Student's Answer: {answer}

Profile Data Context:
{profile_data}

Category: {category}

Please generate 2-3 specific follow-up questions that will:
1. Explore the topic in more depth
2. Clarify any ambiguities in the answer
3. Help gather additional relevant information
4. Be appropriate for the specified category

Return the follow-up questions in the following structured format:
[
  {{
    "question_text": "The follow-up question to ask",
    "expected_response_type": "text/number/date/list/boolean", // expected type of response
    "required": false  // whether this question is required (typically false for follow-ups)
  }},
  // more questions...
]

Focus on creating follow-up questions that are directly related to the original question and answer.
"""

# Template for evaluating answer quality
ANSWER_EVALUATION_PROMPT = """
Evaluate the quality of the following answer to a student profile question:

Question: {question_text}
Category: {category}
Expected Response Type: {expected_response_type}

Student's Answer: {answer_text}

Please evaluate this answer on the following criteria:
1. Completeness (does it fully answer the question?)
2. Relevance (is it directly addressing what was asked?)
3. Specificity (does it provide concrete details rather than generalities?)
4. Helpfulness (will this information be helpful for building the profile?)
5. Authenticity (does it seem genuine and not generic?)

Return your evaluation in the following structured format:
{{
  "quality_score": 0.0-1.0,  // overall quality score between 0 and 1
  "completeness": 0.0-1.0,  // completeness score
  "relevance": 0.0-1.0,  // relevance score
  "specificity": 0.0-1.0,  // specificity score
  "helpfulness": 0.0-1.0,  // helpfulness score
  "authenticity": 0.0-1.0,  // authenticity score
  "needs_follow_up": true/false,  // whether follow-up questions are needed
  "feedback": "Brief feedback on the answer quality and suggestions for improvement"
}}

Be fair and objective in your evaluation.
"""

# Template for extracting structured information from answers
INFORMATION_EXTRACTION_PROMPT = """
Extract structured information from the following student's answer:

Question: {question_text}
Category: {category}
Expected Response Type: {expected_response_type}

Student's Answer: {answer_text}

Please extract key information from this answer that would be relevant for a student profile.
Focus on concrete facts, achievements, experiences, skills, and interests.

Return the extracted information in the following structured JSON format appropriate for the category:

For "academic" category:
{{
  "subjects": [],  // list of academic subjects mentioned
  "grades": [],  // any grades/GPA mentioned
  "achievements": [],  // academic achievements
  "institutions": [],  // schools/colleges mentioned
  "skills": [],  // academic skills mentioned
  "interests": []  // academic interests
}}

For "extracurricular" category:
{{
  "activities": [],  // extracurricular activities
  "roles": [],  // leadership roles or positions
  "timeframes": [],  // duration of involvement
  "achievements": [],  // achievements in these activities
  "skills": []  // skills demonstrated
}}

For "personal" category:
{{
  "background": {},  // relevant background information
  "values": [],  // personal values mentioned
  "strengths": [],  // personal strengths
  "challenges": [],  // challenges overcome
  "interests": []  // personal interests
}}

For "essays" category:
{{
  "topics": [],  // essay topics mentioned
  "themes": [],  // key themes in essays
  "strengths": [],  // strengths of essays
  "areas_for_improvement": []  // areas that need improvement
}}

For "goals" category:
{{
  "short_term": [],  // short-term goals
  "long_term": [],  // long-term goals
  "career": [],  // career goals
  "academic": [],  // academic goals
  "personal": []  // personal development goals
}}

Extract only information that is explicitly stated or strongly implied in the answer.
Do not invent or assume information not present in the text.
"""

# Template for conversation summarization
CONVERSATION_SUMMARY_PROMPT = """
Summarize the following conversation for a student profile:

{conversation_messages}

Based on this conversation, provide a summary of the student's profile with the following structure:
{{
  "summary_text": "A concise summary of the key points from the conversation",
  "key_insights": [
    // List of 3-5 key insights about the student
  ],
  "categories_summary": {{
    "academic": "Summary of academic information",
    "extracurricular": "Summary of extracurricular information",
    "personal": "Summary of personal information",
    "essays": "Summary of essay information",
    "goals": "Summary of goals information"
  }},
  "completion_percentage": 0-100,  // estimated percentage of the profile that's complete
  "missing_information": [
    // List of important information that's still missing
  ],
  "next_steps": [
    // Recommended next steps for completing the profile
  ]
}}

Focus on providing an accurate and helpful summary that highlights the most important aspects of the student's profile.
"""

# Default question templates by category for the TemplateBankQuestionGenerator
DEFAULT_QUESTION_TEMPLATES = {
    "academic": [
        {
            "id": "academic_1",
            "question_text": "What was your GPA in high school?",
            "expected_response_type": "number",
            "required": True,
            "follow_up_questions": [
                "Were there any particular factors that affected your GPA?",
                "How did your GPA change over the course of high school?"
            ]
        },
        {
            "id": "academic_2",
            "question_text": "What were your favorite subjects in high school?",
            "expected_response_type": "text",
            "required": True,
            "follow_up_questions": [
                "Why did you enjoy these subjects?",
                "How did these subjects influence your college plans?"
            ]
        },
        {
            "id": "academic_3",
            "question_text": "What standardized tests have you taken and what were your scores?",
            "expected_response_type": "text",
            "required": True,
            "follow_up_questions": [
                "How did you prepare for these tests?",
                "Are you planning to retake any of these tests?"
            ]
        }
    ],
    "extracurricular": [
        {
            "id": "extracurricular_1",
            "question_text": "What extracurricular activities have you participated in during high school?",
            "expected_response_type": "text",
            "required": True,
            "follow_up_questions": [
                "Which activity was most meaningful to you and why?",
                "What leadership roles did you hold in these activities?"
            ]
        },
        {
            "id": "extracurricular_2",
            "question_text": "Have you participated in any competitions or received any awards?",
            "expected_response_type": "text",
            "required": False,
            "follow_up_questions": [
                "What did you learn from these experiences?",
                "How did these achievements impact your personal growth?"
            ]
        },
        {
            "id": "extracurricular_3",
            "question_text": "Describe any volunteer or community service work you've done.",
            "expected_response_type": "text",
            "required": False,
            "follow_up_questions": [
                "What motivated you to get involved in this service?",
                "How has this service impacted your perspective?"
            ]
        }
    ],
    "personal": [
        {
            "id": "personal_1",
            "question_text": "What are three words that best describe you?",
            "expected_response_type": "text",
            "required": True,
            "follow_up_questions": [
                "Why did you choose these words?",
                "How would your friends or teachers describe you?"
            ]
        },
        {
            "id": "personal_2",
            "question_text": "What challenges have you overcome in your life?",
            "expected_response_type": "text",
            "required": False,
            "follow_up_questions": [
                "How did these challenges affect your academic performance?",
                "What did you learn from overcoming these challenges?"
            ]
        },
        {
            "id": "personal_3",
            "question_text": "What are your hobbies and interests outside of school?",
            "expected_response_type": "text",
            "required": True,
            "follow_up_questions": [
                "How long have you been interested in these activities?",
                "Have these interests influenced your career goals?"
            ]
        }
    ],
    "essays": [
        {
            "id": "essays_1",
            "question_text": "What topics are you considering for your personal statement?",
            "expected_response_type": "text",
            "required": True,
            "follow_up_questions": [
                "Why do you think these topics would make effective essays?",
                "What specific experiences would you highlight in your essay?"
            ]
        },
        {
            "id": "essays_2",
            "question_text": "What do you want colleges to know about you that isn't reflected in your grades and test scores?",
            "expected_response_type": "text",
            "required": True,
            "follow_up_questions": [
                "How could you illustrate these qualities in your essays?",
                "What specific examples could you provide?"
            ]
        },
        {
            "id": "essays_3",
            "question_text": "Have you started drafting any college essays yet?",
            "expected_response_type": "boolean",
            "required": True,
            "follow_up_questions": [
                "What has been the most challenging part of the writing process?",
                "What feedback have you received on your drafts?"
            ]
        }
    ],
    "goals": [
        {
            "id": "goals_1",
            "question_text": "What are your short-term academic goals?",
            "expected_response_type": "text",
            "required": True,
            "follow_up_questions": [
                "How do these goals align with your long-term plans?",
                "What steps are you taking to achieve these goals?"
            ]
        },
        {
            "id": "goals_2",
            "question_text": "What career paths are you considering?",
            "expected_response_type": "text",
            "required": True,
            "follow_up_questions": [
                "What has influenced your interest in these careers?",
                "Have you had any experiences related to these fields?"
            ]
        },
        {
            "id": "goals_3",
            "question_text": "What colleges or universities are you most interested in?",
            "expected_response_type": "text",
            "required": True,
            "follow_up_questions": [
                "Why are you interested in these schools?",
                "How do these schools align with your goals?"
            ]
        }
    ]
} 