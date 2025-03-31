from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.state import (
    ProfileState,
    ProfileSection,
    ProfileStatus,
    create_initial_state
)
from ..services.qa_service import QAService
from ..services.document_service import DocumentService
from ..services.recommender import RecommenderService
from ..core.config import settings

class WorkflowConfig(TypedDict):
    """Configuration for the profile building workflow"""
    session_timeout_minutes: int
    max_interactions: int
    confidence_threshold: float
    human_review_threshold: float

def create_profile_workflow(
    config: WorkflowConfig,
    qa_service: QAService,
    document_service: DocumentService,
    recommender_service: RecommenderService
) -> StateGraph:
    """Create the profile building workflow"""
    
    # Initialize workflow
    workflow = StateGraph(ProfileState)
    
    # Add nodes for major steps
    workflow.add_node("generate_questions", generate_questions)
    workflow.add_node("process_answer", process_answer)
    workflow.add_node("validate_section", validate_section)
    workflow.add_node("request_human_review", request_human_review)
    workflow.add_node("build_profile", build_profile)
    
    # Add conditional edges
    workflow.add_edge("generate_questions", "process_answer")
    workflow.add_edge("process_answer", "validate_section")
    workflow.add_conditional_edges(
        "validate_section",
        should_request_human_review,
        {
            True: "request_human_review",
            False: "generate_questions"
        }
    )
    workflow.add_edge("request_human_review", "generate_questions")
    workflow.add_conditional_edges(
        "generate_questions",
        should_end_session,
        {
            True: "build_profile",
            False: "process_answer"
        }
    )
    workflow.add_edge("build_profile", END)
    
    # Set entry point
    workflow.set_entry_point("generate_questions")
    
    return workflow

async def generate_questions(
    state: ProfileState,
    qa_service: QAService
) -> ProfileState:
    """Generate relevant questions based on current state"""
    try:
        # Get current section
        current_section = state["current_section"]
        
        # Generate questions based on section
        questions = await qa_service.generate_questions(
            section=current_section,
            context=state["context"]
        )
        
        # Update state
        state["current_questions"] = questions
        state["last_updated"] = datetime.utcnow().isoformat()
        
        return state
        
    except Exception as e:
        print(f"Error generating questions: {str(e)}")
        state["error"] = str(e)
        return state

async def process_answer(
    state: ProfileState,
    qa_service: QAService,
    document_service: DocumentService
) -> ProfileState:
    """Process user's answer and extract information"""
    try:
        # Get current answer
        answer = state["current_answer"]
        section = state["current_section"]
        
        # Process answer through Q&A service
        qa_result = await qa_service.process_input(
            answer,
            context=state["context"]
        )
        
        # Extract information
        extracted_info = qa_result["extracted_info"]
        
        # If answer contains document content, analyze it
        if "document_content" in answer:
            doc_result = await document_service.analyze(
                content=answer["document_content"],
                document_type=section,
                metadata={"user_id": state["user_id"]}
            )
            extracted_info.update(doc_result.extracted_info)
        
        # Update section data
        state["sections"][section].update(extracted_info)
        state["sections"][section]["status"] = ProfileStatus.IN_PROGRESS
        
        # Update state
        state["last_updated"] = datetime.utcnow().isoformat()
        state["interaction_count"] += 1
        
        return state
        
    except Exception as e:
        print(f"Error processing answer: {str(e)}")
        state["error"] = str(e)
        return state

async def validate_section(
    state: ProfileState,
    recommender_service: RecommenderService
) -> ProfileState:
    """Validate current section's completeness and quality"""
    try:
        section = state["current_section"]
        section_data = state["sections"][section]
        
        # Get section recommendations
        recommendations = await recommender_service.get_recommendations(
            user_id=state["user_id"],
            profile_data={section: section_data}
        )
        
        # Calculate section quality
        quality_score = recommender_service._calculate_quality_score(
            {section: section_data}
        )
        
        # Update section status
        if quality_score >= config["confidence_threshold"]:
            section_data["status"] = ProfileStatus.COMPLETED
        else:
            section_data["status"] = ProfileStatus.NEEDS_REVIEW
            section_data["recommendations"] = recommendations
        
        # Update state
        state["last_updated"] = datetime.utcnow().isoformat()
        
        return state
        
    except Exception as e:
        print(f"Error validating section: {str(e)}")
        state["error"] = str(e)
        return state

async def request_human_review(
    state: ProfileState
) -> ProfileState:
    """Request human review for current section"""
    try:
        section = state["current_section"]
        section_data = state["sections"][section]
        
        # Prepare review request
        review_request = {
            "section": section,
            "data": section_data,
            "recommendations": section_data.get("recommendations", []),
            "quality_score": section_data.get("quality_score", 0.0)
        }
        
        # Update state with review request
        state["review_requests"].append(review_request)
        state["last_updated"] = datetime.utcnow().isoformat()
        
        return state
        
    except Exception as e:
        print(f"Error requesting human review: {str(e)}")
        state["error"] = str(e)
        return state

async def build_profile(
    state: ProfileState,
    recommender_service: RecommenderService
) -> ProfileState:
    """Build final profile with all sections"""
    try:
        # Get profile summary
        summary = await recommender_service.get_profile_summary(
            user_id=state["user_id"],
            profile_data=state["sections"]
        )
        
        # Update state with summary
        state["summary"] = summary
        state["status"] = "completed"
        state["last_updated"] = datetime.utcnow().isoformat()
        
        return state
        
    except Exception as e:
        print(f"Error building profile: {str(e)}")
        state["error"] = str(e)
        return state

def should_request_human_review(state: ProfileState) -> bool:
    """Determine if human review is needed"""
    try:
        section = state["current_section"]
        section_data = state["sections"][section]
        
        # Check if section needs review
        if section_data["status"] == ProfileStatus.NEEDS_REVIEW:
            return True
        
        # Check quality score
        quality_score = section_data.get("quality_score", 0.0)
        if quality_score < config["human_review_threshold"]:
            return True
        
        return False
        
    except Exception as e:
        print(f"Error checking human review need: {str(e)}")
        return True

def should_end_session(state: ProfileState) -> bool:
    """Determine if the session should end"""
    try:
        # Check timeout
        last_updated = datetime.fromisoformat(state["last_updated"])
        timeout = datetime.timedelta(minutes=config["session_timeout_minutes"])
        if datetime.utcnow() - last_updated > timeout:
            return True
        
        # Check interaction limit
        if state["interaction_count"] >= config["max_interactions"]:
            return True
        
        # Check if all sections are completed
        all_completed = all(
            section["status"] == ProfileStatus.COMPLETED
            for section in state["sections"].values()
        )
        if all_completed:
            return True
        
        return False
        
    except Exception as e:
        print(f"Error checking session end: {str(e)}")
        return True

def update_session_state(state: ProfileState) -> ProfileState:
    """Update session-related state"""
    try:
        # Update interaction count
        state["interaction_count"] += 1
        
        # Update last activity timestamp
        state["last_updated"] = datetime.utcnow().isoformat()
        
        return state
        
    except Exception as e:
        print(f"Error updating session state: {str(e)}")
        return state

def create_workflow_executor(
    config: WorkflowConfig,
    qa_service: QAService,
    document_service: DocumentService,
    recommender_service: RecommenderService
) -> ToolExecutor:
    """Create an executor for the workflow"""
    workflow = create_profile_workflow(
        config=config,
        qa_service=qa_service,
        document_service=document_service,
        recommender_service=recommender_service
    )
    
    return workflow.compile() 