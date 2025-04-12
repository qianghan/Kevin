from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_node import ToolNode
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.state import (
    ProfileState,
    ProfileSection,
    ProfileStatus,
    create_initial_state
)
from ...services.qa_service import QAService
from ...services.document_service import DocumentService
from ...services.recommendation.service import RecommendationService
from ...utils.config_manager import ConfigManager
from ...utils.logging import get_logger

from langchain_core.tools import BaseTool, tool
import json

# Get config instance
config = ConfigManager().get_all()
logger = get_logger(__name__)

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
    recommender_service: RecommendationService
) -> Any:
    """Create the profile building workflow"""
    
    # Create the workflow graph
    workflow = StateGraph(ProfileState)
    
    # Define nodes for the workflow
    async def generate_questions_node(state: ProfileState) -> ProfileState:
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
            logger.error(f"Error generating questions: {str(e)}")
            state["error"] = str(e)
            return state

    async def process_answer_node(state: ProfileState) -> ProfileState:
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
            logger.error(f"Error processing answer: {str(e)}")
            state["error"] = str(e)
            return state

    async def validate_section_node(state: ProfileState) -> ProfileState:
        """Validate current section's completeness and quality"""
        try:
            section = state["current_section"]
            section_data = state["sections"][section]
            
            # Get section recommendations
            recommendations = await recommender_service.generate_recommendations(
                profile_data={section: section_data}
            )
            
            # Update state
            state["last_updated"] = datetime.utcnow().isoformat()
            
            return state
            
        except Exception as e:
            logger.error(f"Error validating section: {str(e)}")
            state["error"] = str(e)
            return state

    async def request_human_review_node(state: ProfileState) -> ProfileState:
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
            logger.error(f"Error requesting human review: {str(e)}")
            state["error"] = str(e)
            return state

    async def build_profile_node(state: ProfileState) -> ProfileState:
        """Build final profile with all sections"""
        try:
            # Generate recommendations based on full profile
            recommendations = await recommender_service.generate_recommendations(
                profile_data=state["sections"]
            )
            
            # Update state
            state["recommendations"] = recommendations
            state["status"] = "completed"
            state["last_updated"] = datetime.utcnow().isoformat()
            
            return state
            
        except Exception as e:
            logger.error(f"Error building profile: {str(e)}")
            state["error"] = str(e)
            return state

    def should_request_human_review(state: ProfileState) -> bool:
        """Determine if human review is needed"""
        try:
            section = state["current_section"]
            section_data = state["sections"][section]
            
            # Check if section needs review
            if section_data.get("status") == ProfileStatus.NEEDS_REVIEW:
                return True
                
            # Check if confidence is below threshold
            if section_data.get("confidence", 0) < config["human_review_threshold"]:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error in review decision: {str(e)}")
            return False

    def should_end_session(state: ProfileState) -> bool:
        """Determine if session should end"""
        try:
            # Check if max interactions reached
            if state["interaction_count"] >= config["max_interactions"]:
                return True
                
            # Check if all sections are completed
            all_completed = True
            for section_name, section_data in state["sections"].items():
                if section_data.get("status") != ProfileStatus.COMPLETED:
                    all_completed = False
                    break
                    
            return all_completed
            
        except Exception as e:
            logger.error(f"Error in end session decision: {str(e)}")
            return False
    
    # Create a process_profile tool
    class ProcessProfileTool(BaseTool):
        """Tool for processing profile data."""
        
        name: str = "process_profile"
        description: str = "Process the profile state and return updated state"
        
        async def _arun(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
            """Process the profile state asynchronously"""
            try:
                # Convert dict to ProfileState
                if isinstance(state_dict, str):
                    state_dict = json.loads(state_dict)
                
                state = ProfileState.model_validate(state_dict)
                
                # Add nodes to workflow
                workflow.add_node("generate_questions", generate_questions_node)
                workflow.add_node("process_answer", process_answer_node)
                workflow.add_node("validate_section", validate_section_node)
                workflow.add_node("request_human_review", request_human_review_node)
                workflow.add_node("build_profile", build_profile_node)
                
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
                
                # Execute workflow with state
                result = await workflow.arun(state)
                return result.model_dump()
                
            except Exception as e:
                logger.error(f"Error processing profile: {str(e)}")
                return {"error": str(e)}
        
        def _run(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
            """Synchronous run not supported"""
            raise NotImplementedError("This tool only supports async execution")
    
    # Create and return the ProcessProfileTool
    process_profile_tool = ProcessProfileTool()
    # Return the tool directly instead of wrapping it in a ToolNode
    return process_profile_tool

def get_profile_summary_tool(workflow):
    """Get a profile summary tool"""
    
    @tool("get_profile_summary")
    def _get_profile_summary(user_id: str) -> str:
        """Get a summary of the user's profile"""
        # Implementation would go here
        return "Profile summary for user " + user_id
    
    return _get_profile_summary

def create_workflow_executor(
    config: WorkflowConfig,
    qa_service: QAService,
    document_service: DocumentService,
    recommender_service: RecommendationService
) -> Any:
    """
    Create a workflow executor.
    
    Args:
        config: Workflow configuration
        qa_service: QA service
        document_service: Document service
        recommender_service: Recommendation service
        
    Returns:
        WorkflowExecutor object with an arun method
    """
    # Create the ProcessProfileTool directly from profile workflow
    # This returns a tool, not a ToolNode
    process_profile_tool = create_profile_workflow(
        config=config,
        qa_service=qa_service,
        document_service=document_service,
        recommender_service=recommender_service
    )
    
    # Create a WorkflowExecutor that wraps the ProcessProfileTool
    return WorkflowExecutor(process_profile_tool)

class WorkflowExecutor:
    """
    A wrapper around a workflow tool that provides a consistent async interface.
    
    This class adapts the tool interface to provide the arun method expected by
    the ConnectionManager.
    """
    
    def __init__(self, process_profile_tool):
        """Initialize with a process_profile_tool."""
        self.process_profile_tool = process_profile_tool
    
    async def arun(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the workflow asynchronously.
        
        Args:
            state: The current state
            
        Returns:
            Updated state
        """
        try:
            logger.debug(f"Running workflow with state: {state}")
            
            # Convert state to dict if needed
            if hasattr(state, 'model_dump'):
                state_dict = state.model_dump()
            else:
                state_dict = state
                
            # Use the ProcessProfileTool directly
            result = await self.process_profile_tool._arun(state_dict)
            logger.debug(f"Workflow execution completed with result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in workflow execution: {str(e)}", exc_info=True)
            raise 