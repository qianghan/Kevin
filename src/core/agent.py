"""
LangGraph agent for Canadian university information retrieval with enhanced workflow.
"""

import os
import sys
import yaml
import operator
import time
import traceback
from typing import List, Dict, Any, Optional, Annotated, Tuple, TypedDict, Sequence, Union, cast
from pydantic import BaseModel, Field
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, FunctionMessage
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from transformers import pipeline
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import project modules
from src.core.document_processor import DocumentProcessor
from src.models.deepseek_client import DeepSeekAPI
from src.utils.web_search import search_web
from src.utils.logger import get_logger, workflow_logger, api_logger

# Configure module logger
logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Define state for the graph
class AgentState(TypedDict):
    """State for the agent graph."""
    messages: Sequence[Any]  # The messages passed between nodes
    documents: List[Document]  # Retrieved documents
    web_documents: List[Document]  # Documents from web search
    has_answered: bool  # Whether the query has been answered
    use_web_search: bool  # Whether to use web search
    query: str  # The original query
    response: Optional[str]  # Generated response
    search_starttime: Optional[float]  # Start time for performance tracking
    thinking_steps: List[Dict[str, Any]]  # Captures internal thinking process for UI

# Initialize LLM based on configuration
def get_llm():
    """Get the LLM to use for the agent."""
    logger.info("Initializing LLM")
    
    try:
        # Check for environment variable to force DeepSeek API usage
        if os.getenv('USE_DEEPSEEK_ONLY', 'false').lower() in ('true', '1', 't'):
            logger.info("USE_DEEPSEEK_ONLY is set - only using DeepSeek API")
            return DeepSeekAPI()
            
        # Load configuration
        with open("config.yaml", 'r') as file:
            config = yaml.safe_load(file)
        
        llm_config = config.get('llm', {})
        provider = llm_config.get('provider', 'deepseek')
        
        logger.info(f"LLM provider configured as: {provider}")
        
        if provider == 'deepseek':
            try:
                # Initialize DeepSeek LLM using our client
                logger.info("Attempting to initialize DeepSeek API client")
                return DeepSeekAPI()
            except Exception as e:
                logger.error(f"Error initializing DeepSeek API: {str(e)}", exc_info=True)
                # No fallback to HuggingFace, force DeepSeek API usage
                logger.critical("DeepSeek API initialization failed and fallback is disabled")
                raise RuntimeError(f"DeepSeek API must be configured properly: {str(e)}")
        else:
            # Force provider to be deepseek
            logger.warning(f"Provider '{provider}' is not supported. Only DeepSeek API is allowed. Switching to DeepSeek.")
            try:
                logger.info("Attempting to initialize DeepSeek API client")
                return DeepSeekAPI()
            except Exception as e:
                logger.error(f"Error initializing DeepSeek API: {str(e)}", exc_info=True)
                raise RuntimeError(f"DeepSeek API must be configured properly: {str(e)}")
    except Exception as e:
        logger.critical(f"Failed to initialize LLM: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to initialize LLM: {str(e)}")

# Router to decide whether to use vector store or web search
def router(state: AgentState) -> AgentState:
    """Decide whether to use vector store or web search."""
    workflow_logger.info("Executing router node to determine search method")
    
    # Initialize thinking steps if not present
    if "thinking_steps" not in state:
        state["thinking_steps"] = []
    
    try:
        # Track performance
        state["search_starttime"] = time.time()
        
        # Get configuration
        with open("config.yaml", 'r') as file:
            config = yaml.safe_load(file)
        
        # Get the last message
        last_message = state["messages"][-1]
        
        if not isinstance(last_message, HumanMessage):
            logger.debug("Last message is not a human message, skipping routing")
            return state
        
        # Extract query from message
        query = last_message.content
        state["query"] = query
        logger.info(f"Processing query: {query}")
        
        # Check for explicit web search keywords
        web_search_keywords = ["recent", "latest", "news", "current", "today", "covid", "2023", "2024"]
        needs_web = any(keyword in query.lower() for keyword in web_search_keywords)
        
        # Add thinking step for routing decision
        thinking = {
            "step": "router",
            "time": time.strftime("%H:%M:%S"),
            "description": "Deciding search method",
            "details": {
                "query": query,
                "keywords_detected": [k for k in web_search_keywords if k in query.lower()],
                "decision": "web search" if needs_web or state.get("use_web_search", False) else "knowledge base"
            }
        }
        state["thinking_steps"].append(thinking)
        
        if needs_web or state.get("use_web_search", False):
            workflow_logger.info(f"Routing query to web search: {query}")
            state["use_web_search"] = True
            state["messages"].append(
                SystemMessage(
                    content=f"I'll search the web for information about: {query}"
                )
            )
        else:
            workflow_logger.info(f"Routing query to vector store: {query}")
            state["use_web_search"] = False
            state["messages"].append(
                SystemMessage(
                    content=f"I'll check my knowledge base for information about: {query}"
                )
            )
    except Exception as e:
        logger.error(f"Error in router node: {str(e)}", exc_info=True)
        # Default to vector store if there's an error
        workflow_logger.warning(f"Error in routing decision, defaulting to vector store: {str(e)}")
        state["use_web_search"] = False
        state["messages"].append(
            SystemMessage(
                content=f"I'll check my knowledge base for information about your query."
            )
        )
        
        # Add error to thinking steps
        if "thinking_steps" in state:
            thinking = {
                "step": "router_error",
                "time": time.strftime("%H:%M:%S"),
                "description": "Error in routing decision",
                "details": {
                    "error": str(e),
                    "fallback": "knowledge base"
                }
            }
            state["thinking_steps"].append(thinking)
    
    return state

# Node for retrieving from vector store
def retrieve_from_vectorstore(state: AgentState) -> AgentState:
    """Retrieve relevant documents from the vector store."""
    workflow_logger.info("Executing vector store retrieval node")
    
    try:
        # Get the query
        query = state["query"]
        logger.info(f"Retrieving documents for query: {query}")
        
        # Initialize document processor
        processor = DocumentProcessor()
        
        # Search for relevant documents
        start_time = time.time()
        documents = processor.search_documents(query, k=5)
        elapsed_time = time.time() - start_time
        
        logger.info(f"Retrieved {len(documents)} documents in {elapsed_time:.2f} seconds")
        workflow_logger.info(f"Vector search retrieved {len(documents)} documents")
        
        # Add documents to state
        state["documents"] = documents
        
        # Log document sources
        sources = []
        for i, doc in enumerate(documents):
            source = doc.metadata.get("source", "Unknown")
            title = doc.metadata.get("title", "Unknown title")
            logger.debug(f"Document {i+1} source: {source}")
            sources.append({"title": title, "source": source})
        
        # Add thinking step
        if "thinking_steps" in state:
            thinking = {
                "step": "vector_search",
                "time": time.strftime("%H:%M:%S"),
                "description": f"Searching knowledge base for: {query}",
                "details": {
                    "documents_found": len(documents),
                    "time_taken": f"{elapsed_time:.2f}s",
                    "sources": sources[:3]  # Just include the first 3 sources to keep it manageable
                }
            }
            state["thinking_steps"].append(thinking)
        
        # Add system message about retrieval
        state["messages"].append(
            SystemMessage(
                content=f"I've retrieved {len(documents)} documents from my knowledge base that might help answer the query."
            )
        )
    except Exception as e:
        logger.error(f"Error in vector store retrieval: {str(e)}", exc_info=True)
        workflow_logger.error(f"Failed to retrieve documents from vector store: {str(e)}")
        
        # Add error to thinking steps
        if "thinking_steps" in state:
            thinking = {
                "step": "vector_search_error",
                "time": time.strftime("%H:%M:%S"),
                "description": "Error searching knowledge base",
                "details": {
                    "error": str(e)
                }
            }
            state["thinking_steps"].append(thinking)
        
        # Handle error gracefully
        state["documents"] = []
        state["messages"].append(
            SystemMessage(
                content=f"I encountered an issue retrieving information from my knowledge base. I'll try to answer based on what I know."
            )
        )
    
    return state

# Node for web search
def perform_web_search(state: AgentState) -> AgentState:
    """Perform web search to find information on the internet."""
    query = state["query"]
    
    logger.info(f"Performing web search for: {query}")
    workflow_logger.info(f"Web search: {query}")
    
    try:
        # Use the search_web function from utils
        start_time = time.time()
        documents = search_web(query)
        elapsed_time = time.time() - start_time
        
        logger.info(f"Web search returned {len(documents)} documents")
        
        # Add the retrieved documents to the state
        state["web_documents"] = documents
        
        # Add thinking step
        if "thinking_steps" in state:
            sources = []
            for i, doc in enumerate(documents[:3]):  # Just get first 3 docs
                source = doc.metadata.get("source", "Unknown")
                title = doc.metadata.get("title", "Unknown title")
                sources.append({"title": title, "source": source})
                
            thinking = {
                "step": "web_search",
                "time": time.strftime("%H:%M:%S"),
                "description": f"Searching the web for: {query}",
                "details": {
                    "documents_found": len(documents),
                    "time_taken": f"{elapsed_time:.2f}s",
                    "sources": sources
                }
            }
            state["thinking_steps"].append(thinking)
        
        if documents:
            return state
        else:
            logger.warning("Web search returned no results")
            
            # Add thinking step for empty results
            if "thinking_steps" in state:
                thinking = {
                    "step": "web_search_empty",
                    "time": time.strftime("%H:%M:%S"),
                    "description": "Web search returned no results",
                    "details": {
                        "query": query
                    }
                }
                state["thinking_steps"].append(thinking)
                
            # Return original state with empty web_documents
            return {**state, "web_documents": []}
    
    except Exception as e:
        logger.error(f"Error in web search: {e}", exc_info=True)
        workflow_logger.error(f"Web search failed: {str(e)}")
        
        # Add error to thinking steps
        if "thinking_steps" in state:
            thinking = {
                "step": "web_search_error",
                "time": time.strftime("%H:%M:%S"),
                "description": "Error searching the web",
                "details": {
                    "error": str(e),
                    "query": query
                }
            }
            state["thinking_steps"].append(thinking)
            
        # Return original state with empty web_documents
        return {**state, "web_documents": []}

# Generate answer based on available documents
def generate_answer(state: AgentState) -> AgentState:
    """Generate an answer based on retrieved documents."""
    workflow_logger.info("Executing answer generation node")
    
    try:
        # Get configuration
        with open("config.yaml", 'r') as file:
            config = yaml.safe_load(file)
        
        # Get the query
        query = state["query"]
        logger.info(f"Generating answer for query: {query}")
        
        # Calculate search time if we were timing
        if "search_starttime" in state:
            search_time = time.time() - state["search_starttime"]
            logger.info(f"Search completed in {search_time:.2f} seconds")
        
        # Determine which documents to use
        if "documents" in state and state["documents"]:
            # Use vector store documents if available
            documents = state["documents"]
            source_type = "knowledge base"
            logger.info(f"Using {len(documents)} documents from knowledge base")
        elif "web_documents" in state and state["web_documents"]:
            # Fall back to web search documents
            documents = state["web_documents"]
            source_type = "web search"
            logger.info(f"Using {len(documents)} documents from web search")
        else:
            # No documents available
            documents = []
            source_type = "limited information"
            logger.warning("No documents available for answer generation")
        
        # Add thinking step
        if "thinking_steps" in state:
            thinking = {
                "step": "answer_generation",
                "time": time.strftime("%H:%M:%S"),
                "description": "Generating answer from documents",
                "details": {
                    "query": query,
                    "document_source": source_type,
                    "document_count": len(documents),
                    "document_titles": [doc.metadata.get("title", "Unknown") for doc in documents[:3]]
                }
            }
            state["thinking_steps"].append(thinking)
        
        workflow_logger.info(f"Generating answer using {source_type} with {len(documents)} documents")
        
        # Prepare context from documents
        context = ""
        for i, doc in enumerate(documents[:5]):  # Limit to 5 documents for performance
            source = doc.metadata.get("source", "Unknown source")
            title = doc.metadata.get("title", "No title")
            context += f"Document {i+1} (from {title}):\n{doc.page_content}\n\n"
        
        # Create system prompt
        system_prompt = """You are a helpful assistant specializing in Canadian university information. 
You provide accurate information to students about programs, admissions, tuition, and scholarships at Canadian universities.

You have access to information from {source_type}. Use this information to provide helpful, accurate answers.
If the information isn't in the provided context, say that you don't have that specific information.
Always cite your sources when providing information.

IMPORTANT: Only provide information that is EXPLICITLY stated in the context below. DO NOT add any details, numbers, 
or facts not directly mentioned in the context. If the information isn't in the context, clearly state that.

Context information:
{context}

User query: {query}
"""
        
        # Get LLM
        llm = get_llm()
        
        # Format the prompt with context and query
        formatted_prompt = system_prompt.format(context=context, query=query, source_type=source_type)
        
        # Generate answer
        logger.debug("Generating answer using LLM")
        start_time = time.time()
        answer = llm.invoke(formatted_prompt)
        elapsed_time = time.time() - start_time
        
        answer_preview = answer[:100] + "..." if len(answer) > 100 else answer
        logger.info(f"Generated answer in {elapsed_time:.2f}s: {answer_preview}")
        
        # Add thinking step for answer
        if "thinking_steps" in state:
            thinking = {
                "step": "answer_completed",
                "time": time.strftime("%H:%M:%S"),
                "description": "Answer generation complete",
                "details": {
                    "time_taken": f"{elapsed_time:.2f}s",
                    "answer_length": len(answer),
                    "answer_preview": answer_preview
                }
            }
            state["thinking_steps"].append(thinking)
        
        # Save answer to state
        state["response"] = answer
        
        workflow_logger.info(f"Answer generation successful (length: {len(answer)} chars)")
    except Exception as e:
        logger.error(f"Error in answer generation: {str(e)}", exc_info=True)
        workflow_logger.error(f"Answer generation failed: {str(e)}")
        
        # Add error to thinking steps
        if "thinking_steps" in state:
            thinking = {
                "step": "answer_generation_error",
                "time": time.strftime("%H:%M:%S"),
                "description": "Error generating answer",
                "details": {
                    "error": str(e)
                }
            }
            state["thinking_steps"].append(thinking)
        
        # Set a generic response in case of error
        state["response"] = "I apologize, but I encountered an issue while generating an answer to your question. Please try asking again or rephrasing your question."
        
    return state

# Finalize the response and update messaging
def finalize_response(state: AgentState) -> AgentState:
    """Finalize the response and add it to the message history."""
    workflow_logger.info("Executing response finalization node")
    
    try:
        # Get the response
        response = state["response"]
        
        logger.info("Finalizing response and updating message history")
        
        # Add response to messages
        state["messages"].append(AIMessage(content=response))
        
        # Mark as answered
        state["has_answered"] = True
        
        # Calculate and log total query time if we were timing
        if "search_starttime" in state:
            total_time = time.time() - state["search_starttime"]
            logger.info(f"Total query processing time: {total_time:.2f} seconds")
            workflow_logger.info(f"Query completed in {total_time:.2f} seconds")
            
            # Add final thinking step with timing
            if "thinking_steps" in state:
                thinking = {
                    "step": "completion",
                    "time": time.strftime("%H:%M:%S"),
                    "description": "Query processing completed",
                    "details": {
                        "total_time": f"{total_time:.2f}s",
                        "thinking_steps_count": len(state["thinking_steps"])
                    }
                }
                state["thinking_steps"].append(thinking)
        
        workflow_logger.info("Response finalization complete")
    except Exception as e:
        logger.error(f"Error in response finalization: {str(e)}", exc_info=True)
        workflow_logger.error(f"Response finalization failed: {str(e)}")
        
        # Add error to thinking steps
        if "thinking_steps" in state:
            thinking = {
                "step": "finalization_error",
                "time": time.strftime("%H:%M:%S"),
                "description": "Error finalizing response",
                "details": {
                    "error": str(e)
                }
            }
            state["thinking_steps"].append(thinking)
        
        # Ensure we still mark the query as answered
        state["has_answered"] = True
    
    return state

# Decision nodes for the graph
def decide_search_method(state: AgentState) -> str:
    """Decide whether to use vector store or web search."""
    decision = "web_search" if state.get("use_web_search", False) else "vectorstore"
    workflow_logger.info(f"Search method decision: {decision}")
    return decision

def decide_after_vectorstore(state: AgentState) -> str:
    """Decide what to do after checking the vector store."""
    decision = "generate_answer" if state.get("is_relevant", False) else "web_search"
    workflow_logger.info(f"After vector store decision: {decision}")
    return decision

def decide_after_grading(state: AgentState) -> str:
    """Decide what to do after grading the documents."""
    decision = "finalize" if state.get("is_hallucination_free", True) else "regenerate"
    workflow_logger.info(f"After grading decision: {decision}")
    return decision

def should_end(state: AgentState) -> str:
    """Decide if the agent should end or continue."""
    # Ensure the has_answered flag is properly checked
    has_answered = state.get("has_answered", False)
    
    # Additional safety check - if we have a response, assume we've answered
    if state.get("response") and not has_answered:
        workflow_logger.warning("Response exists but has_answered is False. Forcing has_answered to True.")
        has_answered = True
        state["has_answered"] = True
    
    decision = "end" if has_answered else "continue"
    workflow_logger.info(f"End decision: {decision} (has_answered: {has_answered})")
    return decision

# Build the graph
def build_agent() -> StateGraph:
    """Build the agent graph with simplified workflow for better performance"""
    logger.info("Building agent graph with simplified workflow for better performance")
    
    try:
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        logger.debug("Adding nodes to graph")
        workflow.add_node("router", router)
        workflow.add_node("retrieve_from_vectorstore", retrieve_from_vectorstore)
        workflow.add_node("perform_web_search", perform_web_search)
        workflow.add_node("generate_answer", generate_answer)
        workflow.add_node("finalize_response", finalize_response)
        
        # Add edges
        logger.debug("Adding edges to graph")
        workflow.add_conditional_edges(
            "router",
            decide_search_method,
            {
                "vectorstore": "retrieve_from_vectorstore",
                "web_search": "perform_web_search"
            }
        )
        
        workflow.add_edge("retrieve_from_vectorstore", "generate_answer")
        workflow.add_edge("perform_web_search", "generate_answer")
        workflow.add_edge("generate_answer", "finalize_response")
        
        workflow.add_conditional_edges(
            "finalize_response",
            should_end,
            {
                "end": END,
                "continue": "router"
            }
        )
        
        # Set entrypoint
        workflow.set_entry_point("router")
        
        logger.info("Agent graph built successfully")
        return workflow
    except Exception as e:
        logger.critical(f"Failed to build agent graph: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to build agent graph: {str(e)}")

class UniversityAgent:
    """Agent for retrieving and answering queries about Canadian universities."""
    
    def __init__(self):
        """Initialize the agent."""
        logger.info("Initializing UniversityAgent")
        try:
            self.graph = build_agent()
            # Simple compile without any extra parameters
            # This version of LangGraph doesn't support config or executor access
            self.graph_instance = self.graph.compile()
            
            logger.info("UniversityAgent initialized successfully")
        except Exception as e:
            logger.critical(f"Failed to initialize UniversityAgent: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to initialize agent: {str(e)}")
    
    def query(self, question: str, use_web_search: bool = False) -> Dict[str, Any]:
        """Query the agent with a question."""
        query_id = f"query_{int(time.time())}"
        logger.info(f"Processing query ID {query_id}: {question}")
        workflow_logger.info(f"[{query_id}] Starting new query: {question}")
        
        start_time = time.time()
        
        try:
            # Initialize state
            state = {
                "messages": [HumanMessage(content=question)],
                "documents": [],
                "web_documents": [],
                "has_answered": False,
                "use_web_search": use_web_search,
                "query": question,
                "response": None,
                "thinking_steps": [
                    {
                        "step": "initialization",
                        "time": time.strftime("%H:%M:%S"),
                        "description": "Starting query processing",
                        "details": {
                            "query": question,
                            "web_search_requested": use_web_search
                        }
                    }
                ]
            }
            
            # Log whether web search is explicitly requested
            if use_web_search:
                logger.info(f"[{query_id}] Web search explicitly requested")
            
            # Run the graph
            workflow_logger.info(f"[{query_id}] Executing agent graph")
            result = self.graph_instance.invoke(state)
            
            # Extract answer
            messages = result["messages"]
            answer = None
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    answer = msg.content
                    # Log a preview of the answer
                    answer_preview = answer[:100] + "..." if len(answer) > 100 else answer
                    logger.info(f"[{query_id}] Generated answer: {answer_preview}")
                    
                    elapsed_time = time.time() - start_time
                    workflow_logger.info(f"[{query_id}] Query completed in {elapsed_time:.2f} seconds")
                    break
            
            if not answer:
                # If no answer found
                logger.warning(f"[{query_id}] No answer found in result messages")
                workflow_logger.warning(f"[{query_id}] Query failed: No answer generated")
                answer = "I couldn't generate an answer to your question."
                
                # Add error thinking step
                if "thinking_steps" in result:
                    result["thinking_steps"].append({
                        "step": "error",
                        "time": time.strftime("%H:%M:%S"),
                        "description": "Failed to generate answer",
                        "details": {
                            "error": "No answer found in messages"
                        }
                    })
            
            # Return both the answer and thinking steps
            return {
                "answer": answer,
                "thinking": result.get("thinking_steps", [])
            }
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_detail = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"[{query_id}] Error processing query: {error_detail}")
            workflow_logger.error(f"[{query_id}] Query failed in {elapsed_time:.2f}s: {str(e)}")
            
            # Create minimal thinking steps for error
            thinking_steps = [
                {
                    "step": "initialization",
                    "time": time.strftime("%H:%M:%S"),
                    "description": "Starting query processing",
                    "details": {
                        "query": question,
                        "web_search_requested": use_web_search
                    }
                },
                {
                    "step": "error",
                    "time": time.strftime("%H:%M:%S"),
                    "description": "Error processing query",
                    "details": {
                        "error": str(e),
                        "time_taken": f"{elapsed_time:.2f}s"
                    }
                }
            ]
            
            return {
                "answer": f"I encountered an error while processing your query: {str(e)}",
                "thinking": thinking_steps
            }

if __name__ == "__main__":
    # Example usage
    logger.info("Starting example usage of UniversityAgent")
    
    try:
        agent = UniversityAgent()
        
        # Query with vector store only
        question1 = "What are the scholarship opportunities for international students at UBC?"
        logger.info(f"Example query 1: {question1}")
        print(f"Question: {question1}")
        answer1 = agent.query(question1)
        print(f"Answer (vector store): {answer1}")
        logger.info("Example query 1 completed successfully")
        
        # Query with web search
        question2 = "What are the latest COVID-19 policies for McGill University?"
        logger.info(f"Example query 2: {question2}")
        print(f"Question: {question2}")
        answer2 = agent.query(question2, use_web_search=True)
        print(f"Answer (web search): {answer2}")
        logger.info("Example query 2 completed successfully")
        print("-" * 80)
    except Exception as e:
        logger.critical(f"Failed in example usage: {str(e)}", exc_info=True)
        print(f"Error in example: {str(e)}") 