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
# Conditionally import transformers only if not using DeepSeek only
if not os.environ.get('USE_DEEPSEEK_ONLY') == '1':
    try:
        from transformers import pipeline
    except UnicodeDecodeError as e:
        print(f"Error importing transformers: {e}")
        print("Continuing without transformers support")
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
    query = state["query"]
    thinking_steps = state.get("thinking_steps", [])
    
    retrieve_start = time.time()
    thinking_steps.append({
        "step": "vector_retrieval_start",
        "time": time.strftime("%H:%M:%S"),
        "description": "Beginning document retrieval from knowledge base",
        "details": {
            "query": query,
            "timestamp": time.time()
        }
    })
    
    try:
        docs = []
        try:
            # Create document processor instance
            doc_processor = DocumentProcessor()
            
            # Get similarity search method
            similarity_search = getattr(doc_processor.get_vectorstore(), "similarity_search_with_score", None)
            if similarity_search:
                search_results = similarity_search(query, k=6)
                
                # Filter results based on similarity score
                docs = [doc for doc, score in search_results if score < 1.2]
                
                # Add a thinking step for search results
                score_details = [{"document": doc.metadata.get("source", "Unknown"), "score": f"{score:.4f}"} for doc, score in search_results]
                thinking_steps.append({
                    "step": "similarity_search_results",
                    "time": time.strftime("%H:%M:%S"),
                    "description": f"Found {len(search_results)} documents, keeping {len(docs)} relevant ones",
                    "details": {
                        "search_results": score_details,
                        "timestamp": time.time()
                    }
                })
            else:
                docs = doc_processor.get_vectorstore().similarity_search(query, k=5)
                thinking_steps.append({
                    "step": "search_results",
                    "time": time.strftime("%H:%M:%S"),
                    "description": f"Retrieved {len(docs)} documents from knowledge base",
                    "details": {
                        "document_count": len(docs),
                        "timestamp": time.time()
                    }
                })
        except Exception as e:
            # Fallback to alternative method
            docs = []
            thinking_steps.append({
                "step": "search_error",
                "time": time.strftime("%H:%M:%S"),
                "description": "Error in primary search method, using fallback",
                "details": {
                    "error": str(e),
                    "timestamp": time.time()
                }
            })
        
        # Add retrieved documents to state
        state["documents"] = docs
        
        # Add a thinking step for completion
        retrieve_time = time.time() - retrieve_start
        thinking_steps.append({
            "step": "vector_retrieval_complete",
            "time": time.strftime("%H:%M:%S"),
            "description": "Document retrieval complete",
            "details": {
                "document_count": len(docs),
                "time_taken": f"{retrieve_time:.2f}s",
                "timestamp": time.time()
            }
        })
        
        # Document preview for debugging
        preview = []
        for i, doc in enumerate(docs[:3]):  # Only show first 3 docs
            source = doc.metadata.get("source", "Unknown")
            content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
            preview.append(f"{i+1}. {source}: {content_preview}")
        
        # Log retrieved documents
        workflow_logger.info(f"Retrieved {len(docs)} documents: {'; '.join(preview)}")
        
    except Exception as e:
        # Log the error
        workflow_logger.error(f"Error retrieving documents: {e}")
        
        # Add error thinking step
        thinking_steps.append({
            "step": "retrieval_error",
            "time": time.strftime("%H:%M:%S"),
            "description": "Error retrieving documents",
            "details": {
                "error": str(e),
                "timestamp": time.time()
            }
        })
    
    # Update thinking steps
    state["thinking_steps"] = thinking_steps
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
    """Generate an answer based on the retrieved documents."""
    query = state["query"]
    documents = state.get("documents", [])
    thinking_steps = state.get("thinking_steps", [])
    
    # Start thinking step
    generate_start = time.time()
    thinking_steps.append({
        "step": "generation_start",
        "time": time.strftime("%H:%M:%S"),
        "description": "Starting answer generation",
        "details": {
            "document_count": len(documents),
            "timestamp": time.time()
        }
    })
    
    try:
        # Get LLM
        llm = get_llm()
        
        # Prepare documents for the context
        if documents:
            # Log the number of documents being used
            workflow_logger.info(f"Generating answer based on {len(documents)} documents")
            
            # Add thinking step for document preparation
            thinking_steps.append({
                "step": "context_preparation",
                "time": time.strftime("%H:%M:%S"),
                "description": "Preparing document context",
                "details": {
                    "document_count": len(documents),
                    "sources": [doc.metadata.get("source", "Unknown") for doc in documents],
                    "timestamp": time.time()
                }
            })
            
            # Prepare document context
            context = "\n\n---\n\n".join([doc.page_content for doc in documents])
        else:
            # No documents found
            context = "No relevant documents found in the knowledge base."
            workflow_logger.warning("No documents available for context")
            
            thinking_steps.append({
                "step": "no_context",
                "time": time.strftime("%H:%M:%S"),
                "description": "No relevant documents found for context",
                "details": {
                    "timestamp": time.time()
                }
            })
        
        # Create the prompt with custom instructions
        prompt_template = """
        You are Kevin, a professional consultant specialized in Canadian university education. 
        You provide accurate, comprehensive, and helpful information about Canadian universities, 
        including admissions, programs, tuition, scholarships, campus life, and more.
        
        Use the following context to answer the question. If the context doesn't contain relevant 
        information to fully answer the question, acknowledge the limitations of your knowledge 
        and suggest what additional information might be helpful.
        
        Context:
        {context}
        
        Question: {question}
        
        Your answer should be:
        1. Comprehensive yet concise
        2. Structured with clear sections when appropriate
        3. Professional and helpful in tone
        4. Accurate and based only on the provided context
        
        Answer:
        """
        
        # Add thinking step for prompt creation
        thinking_steps.append({
            "step": "prompt_creation",
            "time": time.strftime("%H:%M:%S"),
            "description": "Created prompt for answer generation",
            "details": {
                "context_length": len(context),
                "timestamp": time.time()
            }
        })
        
        # Create and format the prompt
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Format the prompt with our variables
        formatted_prompt = prompt.format(context=context, question=query)
        
        # Generate answer
        workflow_logger.info("Generating answer with LLM")
        thinking_steps.append({
            "step": "llm_generation",
            "time": time.strftime("%H:%M:%S"),
            "description": "Sending query to language model",
            "details": {
                "model": getattr(llm, "model_name", "unknown"),
                "timestamp": time.time()
            }
        })
        
        # Invoke LLM
        answer = llm.invoke(formatted_prompt)
        
        # Measure generation time
        generate_time = time.time() - generate_start
        
        # Add thinking step for answer generation
        thinking_steps.append({
            "step": "answer_generated",
            "time": time.strftime("%H:%M:%S"),
            "description": "Answer successfully generated",
            "details": {
                "answer_length": len(answer),
                "time_taken": f"{generate_time:.2f}s",
                "timestamp": time.time()
            }
        })
        
        # Create an AI message with the answer
        ai_message = AIMessage(content=answer)
        
        # Update state with the answer and thinking steps
        state["messages"].append(ai_message)
        state["thinking_steps"] = thinking_steps
        state["has_answered"] = True
        state["response"] = answer
        
        # Log completion
        workflow_logger.info(f"Answer generated in {generate_time:.2f}s")
        
        return state
        
    except Exception as e:
        # Log error
        workflow_logger.error(f"Error generating answer: {e}")
        
        # Add error thinking step
        thinking_steps.append({
            "step": "generation_error",
            "time": time.strftime("%H:%M:%S"),
            "description": "Error generating answer",
            "details": {
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": time.time()
            }
        })
        
        # Create an error message
        error_message = f"I apologize, but I encountered an error while generating your answer: {str(e)}"
        ai_message = AIMessage(content=error_message)
        
        # Update state with error
        state["messages"].append(ai_message)
        state["thinking_steps"] = thinking_steps
        state["has_answered"] = True
        state["response"] = error_message
        
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
                            "web_search_requested": use_web_search,
                            "timestamp": time.time()
                        }
                    }
                ]
            }
            
            # Log whether web search is explicitly requested
            if use_web_search:
                logger.info(f"[{query_id}] Web search explicitly requested")
                # Add a thinking step for web search request
                state["thinking_steps"].append({
                    "step": "web_search_requested",
                    "time": time.strftime("%H:%M:%S"),
                    "description": "Web search explicitly requested by user",
                    "details": {
                        "timestamp": time.time()
                    }
                })
            
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
                    
                    # Add a final thinking step for completion
                    if "thinking_steps" in result:
                        result["thinking_steps"].append({
                            "step": "completion",
                            "time": time.strftime("%H:%M:%S"),
                            "description": "Response generation complete",
                            "details": {
                                "elapsed_time": f"{elapsed_time:.2f}s",
                                "answer_length": len(answer),
                                "timestamp": time.time()
                            }
                        })
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
            
            # Create more detailed thinking steps for error
            thinking_steps = [
                {
                    "step": "initialization",
                    "time": time.strftime("%H:%M:%S"),
                    "description": "Starting query processing",
                    "details": {
                        "query": question,
                        "web_search_requested": use_web_search,
                        "timestamp": time.time()
                    }
                },
                {
                    "step": "error",
                    "time": time.strftime("%H:%M:%S"),
                    "description": "Error processing query",
                    "details": {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "time_taken": f"{elapsed_time:.2f}s",
                        "timestamp": time.time()
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