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
import inspect
# Removing the problematic import temporarily
# from langchain.callbacks.base import BaseCallbackHandler
# from langchain.callbacks.manager import CallbackManager

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

# Global variable to store the last answer for backup
_LAST_ANSWER = None

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

def _update_thinking_steps(agent_instance, state, new_thinking_step):
    """Update the thinking steps in both the state and the agent instance for real-time tracking."""
    if "thinking_steps" not in state:
        state["thinking_steps"] = []
    
    # Add the new thinking step to the state
    state["thinking_steps"].append(new_thinking_step)
    
    # Update the agent's latest_thinking_steps for real-time display in the UI
    if hasattr(agent_instance, 'latest_thinking_steps'):
        agent_instance.latest_thinking_steps = state["thinking_steps"].copy()
    
    return state

def router(state: AgentState) -> AgentState:
    """Route the conversation based on the query type."""
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
            state["use_web_search"] = False
            return state

        # Extract query from message
        query = last_message.content
        state["query"] = query
        logger.info(f"Processing query: {query}")
        
        # Check for explicit web search keywords
        web_search_keywords = ["recent", "latest", "news", "current", "today", "covid", "2023", "2024"]
        needs_web = any(keyword in query.lower() for keyword in web_search_keywords)
        
        # Prepare timing for thinking step
        end_time = time.time()
        duration_ms = int((end_time - state["search_starttime"]) * 1000)
        
        # Get the agent instance to update real-time thinking steps
        agent_instance = None
        for frame in inspect.stack():
            if 'self' in frame.frame.f_locals and isinstance(frame.frame.f_locals['self'], UniversityAgent):
                agent_instance = frame.frame.f_locals['self']
                break
        
        # Add thinking step for routing decision
        thinking = {
            "type": "router",
            "time": time.strftime("%H:%M:%S"),
            "description": "Deciding search method",
            "duration_ms": duration_ms,
            "content": f"Query: {query}\nKeywords detected: {[k for k in web_search_keywords if k in query.lower()]}\nDecision: {'web search' if needs_web or state.get('use_web_search', False) else 'knowledge base'}"
        }
        
        # Update thinking steps both in state and agent instance
        if "thinking_steps" not in state:
            state["thinking_steps"] = []
        state["thinking_steps"].append(thinking)
        
        # Update the agent's real-time thinking steps
        if agent_instance and hasattr(agent_instance, 'latest_thinking_steps'):
            agent_instance.latest_thinking_steps = state["thinking_steps"].copy()
        
        if needs_web or state.get("use_web_search", False):
            workflow_logger.info(f"Routing query to web search: {query}")
            workflow_logger.info(f"Search method decision: web_search")
            state["use_web_search"] = True
            state["messages"].append(
                SystemMessage(
                    content=f"I'll search the web for information about: {query}"
                )
            )
            # Instead of returning a string, we'll set a routing key in the state
            state["next"] = "web_search"
            return state
        else:
            workflow_logger.info(f"Routing query to vector store: {query}")
            workflow_logger.info(f"Search method decision: vector_search")
            state["use_web_search"] = False
            state["messages"].append(
                SystemMessage(
                    content=f"I'll check my knowledge base for information about: {query}"
                )
            )
            # Instead of returning a string, we'll set a routing key in the state
            state["next"] = "vector_search"
            return state
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
                "type": "router_error",
                "time": time.strftime("%H:%M:%S"),
                "description": "Error in routing decision",
                "duration_ms": 0,
                "content": f"Error: {str(e)}\nFallback: knowledge base",
                "error": True
            }
            state["thinking_steps"].append(thinking)
            
            # Update the agent's real-time thinking steps
            if agent_instance and hasattr(agent_instance, 'latest_thinking_steps'):
                agent_instance.latest_thinking_steps = state["thinking_steps"].copy()
        
        # Instead of returning a string, set a routing key in the state
        state["next"] = "vector_search"
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
def web_search(state: AgentState) -> AgentState:
    """Search the web for information."""
    workflow_logger.info("Web search: " + state.get("query", "No query found"))
    
    # Extract query from state
    query = state.get("query", "")
    if not query:
        # Try to get query from the last message
        last_message = state["messages"][-1]
        if isinstance(last_message, HumanMessage):
            query = last_message.content
            state["query"] = query
    
    logger.info(f"Performing web search for: {query}")
    
    # Get the agent instance to update real-time thinking steps
    agent_instance = None
    for frame in inspect.stack():
        if 'self' in frame.frame.f_locals and isinstance(frame.frame.f_locals['self'], UniversityAgent):
            agent_instance = frame.frame.f_locals['self']
            break
    
    try:
        # Get thinking steps list
        thinking_steps = state.get("thinking_steps", [])
        
        # Start time for this step
        step_start_time = time.time()
        
        # Add a thinking step for search request
        search_step = {
            "type": "web_search_request",
            "time": time.strftime("%H:%M:%S"),
            "description": "Searching the web",
            "duration_ms": 0,  # Will update after search completes
            "content": f"Query: {query}"
        }
        thinking_steps.append(search_step)
        
        # Update real-time thinking steps
        if agent_instance and hasattr(agent_instance, 'latest_thinking_steps'):
            agent_instance.latest_thinking_steps = thinking_steps.copy()
        
        # Perform the web search
        from src.utils.web_search import search_web
        search_start = time.time()
        results = search_web(query)
        search_duration = time.time() - search_start
        
        # Update the search step with duration
        search_step["duration_ms"] = int(search_duration * 1000)
        
        # Create Document objects from results
        web_documents = []
        for result in results:
            # Check if result is already a Document
            if isinstance(result, Document):
                web_documents.append(result)
            elif isinstance(result, dict):
                # If it's a dictionary, convert to Document
                content = result.get("content", result.get("snippet", ""))
                metadata = {
                    "source": result.get("url", result.get("link", "Web search")),
                    "title": result.get("title", "Web result"),
                    "score": result.get("score", 1.0)
                }
                web_documents.append(Document(page_content=content, metadata=metadata))
        
        # Add a thinking step for search results
        sources = ", ".join([doc.metadata.get("title", "Untitled") for doc in web_documents])
        thinking_steps.append({
            "type": "web_search_results",
            "time": time.strftime("%H:%M:%S"),
            "description": f"Found {len(web_documents)} web results",
            "duration_ms": int((time.time() - step_start_time) * 1000),
            "content": f"Sources: {sources}"
        })
        
        # Store results in state
        state["web_documents"] = web_documents
        
        # If no documents were found in both vectorstore and web, log that
        if not web_documents and not state.get("documents", []):
            thinking_steps.append({
                "type": "no_results",
                "time": time.strftime("%H:%M:%S"),
                "description": "No information found",
                "duration_ms": 0,
                "content": "No documents were found from either vectorstore or web search."
            })
        
        # Update state
        state["thinking_steps"] = thinking_steps
        
        # Update real-time thinking steps
        if agent_instance and hasattr(agent_instance, 'latest_thinking_steps'):
            agent_instance.latest_thinking_steps = thinking_steps.copy()
        
        logger.info(f"Web search returned {len(web_documents)} documents")
        return state
        
    except Exception as e:
        logger.error(f"Error in web search: {e}")
        
        # Get thinking steps list
        thinking_steps = state.get("thinking_steps", [])
        
        # Add error thinking step
        thinking_steps.append({
            "type": "error",
            "time": time.strftime("%H:%M:%S"),
            "description": "Error in web search",
            "duration_ms": 0,
            "content": f"Error: {str(e)}",
            "error": True
        })
        
        # Update state
        state["thinking_steps"] = thinking_steps
        
        # Update real-time thinking steps
        if agent_instance and hasattr(agent_instance, 'latest_thinking_steps'):
            agent_instance.latest_thinking_steps = thinking_steps.copy()
        
        return state

# Generate answer based on available documents
def generate_answer(state: AgentState) -> AgentState:
    """Generate an answer using the LLM."""
    workflow_logger.info("Generating answer with LLM")
    
    query = state.get("query", "")
    if not query:
        # Try to get query from the last message
        if state["messages"] and len(state["messages"]) > 0:
            last_message = state["messages"][-1]
            if isinstance(last_message, HumanMessage):
                query = last_message.content
                state["query"] = query
    
    # Get the agent instance to update real-time thinking steps
    agent_instance = None
    for frame in inspect.stack():
        if 'self' in frame.frame.f_locals and isinstance(frame.frame.f_locals['self'], UniversityAgent):
            agent_instance = frame.frame.f_locals['self']
            break
    
    # Combine all available documents
    documents = state.get("documents", []).copy()
    web_documents = state.get("web_documents", [])
    if web_documents:
        documents.extend(web_documents)
    
    # Get thinking steps
    thinking_steps = state.get("thinking_steps", [])
    start_time = time.time()
    
    # Log the retrieval process info
    if not documents:
        workflow_logger.warning("No documents available for context")
        
        # Add thinking step for no documents
        thinking_steps.append({
            "type": "no_documents",
            "time": time.strftime("%H:%M:%S"),
            "description": "No context documents available",
            "duration_ms": 0,
            "content": "Answer will be generated based solely on the query, without additional context."
        })
        
        # Update real-time thinking steps
        if agent_instance and hasattr(agent_instance, 'latest_thinking_steps'):
            agent_instance.latest_thinking_steps = thinking_steps.copy()
    else:
        # Add thinking step for document retrieval
        thinking_steps.append({
            "type": "documents_retrieved",
            "time": time.strftime("%H:%M:%S"),
            "description": f"Retrieved {len(documents)} documents for context",
            "duration_ms": int((time.time() - start_time) * 1000),
            "content": f"Using {len(documents)} documents as context for generating answer."
        })
        
        # Update real-time thinking steps
        if agent_instance and hasattr(agent_instance, 'latest_thinking_steps'):
            agent_instance.latest_thinking_steps = thinking_steps.copy()
    
    # Initialize LLM if not done already
    logger.info("Initializing LLM")
    try:
        # First, set up the language model
        # Check if we're in DeepSeek-only mode
        if os.environ.get('USE_DEEPSEEK_ONLY') == '1':
            logger.info("USE_DEEPSEEK_ONLY is set - only using DeepSeek API")
            from src.models.deepseek_client import DeepSeekAPI
            llm = DeepSeekAPI()  # Load with default settings from config
        else:
            # Otherwise, try loading the local LLM
            try:
                llm = HuggingFacePipeline(
                    pipeline=pipeline(
                        "text-generation",
                        model="mistralai/Mistral-7B-Instruct-v0.1",
                        tokenizer="mistralai/Mistral-7B-Instruct-v0.1",
                        torch_dtype=torch.bfloat16,
                        device_map="auto",
                        max_new_tokens=512,
                        do_sample=True,
                        temperature=0.7,
                        top_k=50,
                        top_p=0.95
                    )
                )
            except Exception as e:
                logger.error(f"Failed to load Mistral: {e}. Falling back to DeepSeek API.")
                from src.models.deepseek_client import DeepSeekAPI
                llm = DeepSeekAPI()  # Load with default settings from config
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        raise RuntimeError(f"Failed to initialize LLM: {e}")
    
    # Add thinking step for prompt creation
    thinking_steps.append({
        "type": "prompt_creation",
        "time": time.strftime("%H:%M:%S"),
        "description": "Creating LLM prompt",
        "duration_ms": int((time.time() - start_time) * 1000),
        "content": f"Preparing prompt with {len(documents)} documents"
    })
    
    # Update real-time thinking steps
    if agent_instance and hasattr(agent_instance, 'latest_thinking_steps'):
        agent_instance.latest_thinking_steps = thinking_steps.copy()
    
    # Now create the prompt
    prompt = create_prompt_for_llm(query, documents)
    
    # Log the prompt for debugging
    if os.environ.get('LOG_PROMPTS'):
        logger.debug(f"Prompt: {prompt}")
    
    # Update thinking step right before LLM call
    llm_start_time = time.time()
    thinking_steps.append({
        "type": "llm_call",
        "time": time.strftime("%H:%M:%S"),
        "description": "Calling LLM for answer generation",
        "duration_ms": 0,  # Will be updated after call
        "content": "Sending prompt to language model..."
    })
    
    # Update real-time thinking steps
    if agent_instance and hasattr(agent_instance, 'latest_thinking_steps'):
        agent_instance.latest_thinking_steps = thinking_steps.copy()
    
    # Generate the answer using the LLM
    messages = [SystemMessage(content=prompt)]
    if len(state["messages"]) >= 1:
        # Add the last user message if available
        messages.append(state["messages"][-1])
    
    # Create a streaming callback handler to update thinking steps
    streaming_content = []
    first_token_received = False
    first_token_time = None
    
    # Simplified placeholder for callback handler - not extending BaseCallbackHandler
    class StreamingCallbackHandler:
        def on_llm_new_token(self, token: str, **kwargs) -> None:
            nonlocal first_token_received, first_token_time, streaming_content
            if not first_token_received:
                first_token_received = True
                first_token_time = time.time()
                # Update thinking step with first token time
                thinking_steps[-1]["description"] = "Receiving answer stream from LLM"
                thinking_steps[-1]["content"] = f"First token received in {first_token_time - llm_start_time:.2f}s"
                # Update real-time thinking steps when first token arrives
                if agent_instance and hasattr(agent_instance, 'latest_thinking_steps'):
                    agent_instance.latest_thinking_steps = thinking_steps.copy()
            
            # Add token to streaming content
            streaming_content.append(token)
            
            # Update thinking step content with the current answer so far
            if len(streaming_content) % 10 == 0:  # Update every 10 tokens to reduce overhead
                current_content = "".join(streaming_content)
                preview = current_content[:500] + "..." if len(current_content) > 500 else current_content
                thinking_steps[-1]["content"] = f"Answer being generated: {preview}"
                thinking_steps[-1]["duration_ms"] = int((time.time() - llm_start_time) * 1000)
                # Update real-time thinking steps
                if agent_instance and hasattr(agent_instance, 'latest_thinking_steps'):
                    agent_instance.latest_thinking_steps = thinking_steps.copy()
    
    # Create simplified callback handler - just an instance, not a manager
    callback_handler = StreamingCallbackHandler()
    
    try:
        # Handle different LLM input formats with streaming enabled
        if hasattr(llm, 'invoke'):
            logger.info(f"Calling LLM with invoke method - message types: {[type(m).__name__ for m in messages]}")
            
            # Enable streaming for the DeepSeek API
            if hasattr(llm, "_streaming_call"):
                logger.info("Using streaming mode for LLM call")
                # If it's the DeepSeek API, use streaming
                # Pass our callback handler directly to collect tokens
                response = llm.invoke(messages, stream=True, callbacks=[callback_handler])
                
                # Wait for streaming to complete to collect the full response
                # This is not optimal but ensures compatibility
                time.sleep(0.5)  # Small wait to ensure streaming starts
                
                # For streaming, the answer should be in streaming_content,
                # but if it's empty, try to get it from the response
                answer = "".join(streaming_content)
                
                # If we didn't collect any content through callbacks
                if not answer and isinstance(response, str):
                    answer = response
                
                logger.info(f"Streaming complete, collected answer length: {len(answer)}")
            else:
                # For non-streaming LLMs
                response = llm.invoke(messages)
                
                # Extract answer from response based on its type
                if hasattr(response, 'content'):
                    # LangChain AIMessage format
                    answer = response.content
                    logger.info(f"Extracted answer from AIMessage.content: {answer[:50]}...")
                elif isinstance(response, str):
                    # String response
                    answer = response
                    logger.info(f"Using string response directly: {answer[:50]}...")
                elif isinstance(response, dict):
                    # Dictionary response
                    answer = response.get('output', response.get('content', response.get('text', str(response))))
                    logger.info(f"Extracted answer from dict with keys {list(response.keys())}: {answer[:50]}...")
                else:
                    # Fallback - convert to string
                    answer = str(response)
                    logger.info(f"Converted unknown response type to string: {answer[:50]}...")
        else:
            # Fallback to older _call method if invoke not available
            logger.info("Falling back to _call method")
            combined_prompt = "\n\n".join([m.content for m in messages])
            answer = llm(combined_prompt)
            logger.info(f"Got answer from _call: {answer[:50]}...")
    except Exception as e:
        logger.error(f"Error generating answer: {e}", exc_info=True)
        # Add error to thinking steps
        thinking_steps.append({
            "type": "error",
            "time": time.strftime("%H:%M:%S"),
            "description": "Error generating answer",
            "duration_ms": int((time.time() - llm_start_time) * 1000),
            "content": f"Error: {e}",
            "error": True
        })
        raise
    
    # Calculate duration
    llm_duration_ms = int((time.time() - llm_start_time) * 1000)
    
    # Update the LLM call thinking step with the duration
    thinking_steps[-1]["duration_ms"] = llm_duration_ms
    thinking_steps[-1]["content"] = f"LLM call completed in {llm_duration_ms/1000:.2f}s"
    
    # Add thinking step for answer generation
    thinking_steps.append({
        "type": "answer_processing",
        "time": time.strftime("%H:%M:%S"),
        "description": "Processing LLM response",
        "duration_ms": int((time.time() - llm_start_time) * 1000),
        "content": f"Answer generated: {answer[:100]}..." if answer else "No answer generated."
    })
    
    # Update real-time thinking steps
    if agent_instance and hasattr(agent_instance, 'latest_thinking_steps'):
        agent_instance.latest_thinking_steps = thinking_steps.copy()
    
    # Store the answer in the state - double check that it's not None
    if answer is None:
        logger.warning("Answer is None, using fallback message")
        answer = "I'm unable to generate a response at this time. Please try again."
    
    logger.info(f"Storing answer in state: {answer[:100]}..." if answer else "No answer to store")
    state["answer"] = answer
    state["output"] = answer
    state["response"] = answer  # Also store in response field
    
    # Make sure we mark the state as having answered
    state["has_answered"] = True
    
    # Store the answer directly in the agent instance if available
    if agent_instance:
        agent_instance.last_answer = answer
    
    # Add thinking step for completion
    thinking_steps.append({
        "type": "completion",
        "time": time.strftime("%H:%M:%S"),
        "description": "Answer ready",
        "duration_ms": int((time.time() - start_time) * 1000),
        "content": f"Total time: {(time.time() - start_time):.2f}s"
    })
    
    # Update state with thinking steps
    state["thinking_steps"] = thinking_steps
    
    # Update real-time thinking steps
    if agent_instance and hasattr(agent_instance, 'latest_thinking_steps'):
        agent_instance.latest_thinking_steps = thinking_steps.copy()
    
    return state

# Finalize the response and update messaging
def finalize_response(state: AgentState) -> AgentState:
    """Finalize the response and update the message history."""
    workflow_logger.info("Executing response finalization node")
    
    # Log state for debugging
    logger.info(f"Finalizing response and updating message history")
    logger.info(f"State keys: {list(state.keys())}")
    
    # Extract the agent instance to update real-time thinking steps
    agent_instance = None
    for frame in inspect.stack():
        if 'self' in frame.frame.f_locals and isinstance(frame.frame.f_locals['self'], UniversityAgent):
            agent_instance = frame.frame.f_locals['self']
            break
    
    # Check if we have an output or answer
    output = state.get("output")
    answer = state.get("answer")
    
    logger.info(f"Output found in state: {type(output).__name__ if output else 'Not found'}")
    logger.info(f"Answer found in state: {type(answer).__name__ if answer else 'Not found'}")
    
    # Try different keys to find a response
    if output:
        logger.info(f"Checking output key: Found")
        response = output
    elif answer:
        logger.info(f"Checking answer key: Found")
        response = answer
    elif "response" in state and state["response"]:
        logger.info(f"Checking response key: Found")
        response = state["response"]
    elif agent_instance and hasattr(agent_instance, 'last_answer') and agent_instance.last_answer:
        # Try getting from agent instance
        logger.info(f"Using agent instance last_answer")
        response = agent_instance.last_answer
    else:
        # If no response in state, generate a default one
        logger.warning("No response found in state, using default message")
        response = "I'm unable to generate a response at this time. Please try again."
    
    # Log the response for debugging
    logger.info(f"Using response: {response[:50]}..." if response else "No response")
    
    # Store response in state
    state["response"] = response
    state["output"] = response
    state["answer"] = response
    
    # Add response as AI message if not already present
    if isinstance(state.get("messages", []), list):
        # Check if the last message is already an AI message - if so, replace it
        if state["messages"] and hasattr(state["messages"][-1], "type") and state["messages"][-1].type == "ai":
            # Replace the last AI message
            state["messages"][-1] = AIMessage(content=response)
            logger.info(f"Replaced last AI message")
        else:
            # Add new AI message
            state["messages"].append(AIMessage(content=response))
            logger.info(f"Added response as AIMessage")
    
    # Mark state as having answered
    state["has_answered"] = True
    
    workflow_logger.info("Query completed in %.2f seconds", 
                        time.time() - state.get("search_starttime", time.time()))
    workflow_logger.info("Response finalization complete")
    
    return state

# Decision nodes for the graph
def decide_search_method(state: AgentState) -> str:
    """Decide which search method to use based on the 'next' key in state."""
    # Use the "next" key which was set in the router
    return state.get("next", "vectorstore")

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
        # Create graph with proper state transfer
        workflow = StateGraph(AgentState)
        
        # Add nodes - don't use wrappers as they may be causing the state loss issue
        logger.debug("Adding nodes to graph")
        workflow.add_node("router", router)
        workflow.add_node("retrieve_from_vectorstore", retrieve_from_vectorstore)
        workflow.add_node("web_search", web_search)
        workflow.add_node("generate_answer", generate_answer)
        workflow.add_node("finalize_response", finalize_response)
        
        # Add edges
        logger.debug("Adding edges to graph")
        workflow.add_conditional_edges(
            "router",
            decide_search_method,
            {
                "vector_search": "retrieve_from_vectorstore",
                "web_search": "web_search"
            }
        )
        
        workflow.add_edge("retrieve_from_vectorstore", "generate_answer")
        workflow.add_edge("web_search", "generate_answer")
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
        logger.error(f"Error building agent graph: {e}", exc_info=True)
        raise

class UniversityAgent:
    """University information agent that uses LangChain to answer questions."""
    
    def __init__(self):
        """Initialize the agent with the state graph."""
        logger.info("Initializing UniversityAgent")
        
        # Build the graph
        try:
            # Create the state graph
            self.graph = build_agent()
            
            # Check if we need to compile the graph
            if hasattr(self.graph, 'compile'):
                logger.info("Compiling graph (LangGraph v0.0.x)")
                self.graph_instance = self.graph.compile()
                self._run_method = self._run_compiled
            else:
                logger.info("Using uncompiled graph (LangGraph >= v0.1.x)")
                self._run_method = self._run_directly
            
            # Initialize thinking steps for real-time updates
            self.latest_thinking_steps = []
            
            # Initialize last_answer for state preservation
            self.last_answer = None
            
            # Run a sanity check to make sure the graph is configured correctly
            logger.debug(f"Graph methods: {[m for m in dir(self.graph) if not m.startswith('_') and callable(getattr(self.graph, m))]}")
            logger.info("UniversityAgent initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing agent: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize agent: {e}")
    
    def _run_compiled(self, state):
        """Run the graph using the compiled instance (LangGraph v0.0.x)"""
        logger.debug("Running graph using compiled instance")
        return self.graph_instance.invoke(state)
    
    def _run_directly(self, state):
        """Run the graph directly (LangGraph >= v0.1.x)"""
        logger.debug("Running graph directly")
        return self.graph.run(state)
        
    def _custom_workflow(self, state):
        """Directly execute the workflow functions to ensure state preservation"""
        logger.info("Running custom workflow implementation")
        
        # Step 1: Route the query
        route_decision = decide_search_method(state)
        logger.info(f"Routing decision: {route_decision}")
        
        # Step 2: Perform search based on routing decision
        if route_decision == "vector_search":
            state = retrieve_from_vectorstore(state)
        else:  # web_search
            state = web_search(state)
            
        # Step 3: Generate answer
        state = generate_answer(state)
        
        # Make sure the answer is preserved
        if "answer" in state and state["answer"]:
            answer = state["answer"]
            # Store answer in instance variable for debugging and fallback
            self.last_answer = answer
            logger.info(f"Saving answer for preservation: {answer[:100]}...")
            
            # Ensure it's in all relevant state keys
            state["answer"] = answer
            state["output"] = answer
            state["response"] = answer
        
        # Step 4: Finalize response
        state = finalize_response(state)
        
        return state
        
    def query(self, question: str, use_web_search: bool = False) -> Dict[str, Any]:
        """
        Process a query through the agent.
        
        Args:
            question: The query to process
            use_web_search: Whether to use web search
            
        Returns:
            Dict containing the answer and other information
        """
        # Generate a unique ID for this query
        query_id = f"query_{int(time.time())}"
        logger.info(f"Processing query ID {query_id}: {question}")
        
        # Initialize state
        state = {
            "messages": [HumanMessage(content=question)],
            "documents": [],
            "web_documents": [],
            "has_answered": False,
            "use_web_search": use_web_search,
            "query": question,
            "search_starttime": time.time(),
            "thinking_steps": [],
            "output": None,  # Initialize both output and answer fields
            "answer": None,
            "response": None
        }
        
        # Initialize thinking steps with query start
        state["thinking_steps"].append({
            "type": "start",
            "time": time.strftime("%H:%M:%S"),
            "description": "Starting query processing",
            "duration_ms": 0,
            "content": ""
        })
        
        # If web search is explicitly requested, add a thinking step
        if use_web_search:
            state["thinking_steps"].append({
                "type": "web_search_requested",
                "time": time.strftime("%H:%M:%S"),
                "description": "Web search explicitly requested by user",
                "duration_ms": 0,
                "content": ""
            })
            logger.info(f"[{query_id}] Web search explicitly requested")
        
        # Reset latest thinking steps for UI
        self.latest_thinking_steps = state["thinking_steps"].copy()
        
        # Set default result in case execution fails
        result = {
            "answer": "I'm sorry, but I wasn't able to process your query.",
            "query": question,
            "thinking": state["thinking_steps"],
        }
        
        # Wrap in try-except to handle any errors
        try:
            workflow_logger.info(f"[{query_id}] Starting new query: {question}")
            if use_web_search:
                workflow_logger.info(f"[{query_id}] Web search explicitly requested")
            
            workflow_logger.info(f"[{query_id}] Executing agent graph")
            
            # Execute custom workflow instead of using the graph
            end_state = self._custom_workflow(state)
            
            # Log ALL state keys at the end for debugging
            logger.info(f"End state keys: {list(end_state.keys())}")
            
            # Extract answer from all possible locations
            answer = None
            
            # Check each possible key for an answer
            for key in ['answer', 'output', 'response']:
                if key in end_state and end_state[key]:
                    answer = end_state[key]
                    logger.info(f"Found answer in '{key}': {answer[:100]}...")
                    break
            
            # If answer is still None, check messages as a last resort
            if answer is None and 'messages' in end_state and len(end_state['messages']) > 1:
                for msg in reversed(end_state['messages']):
                    if hasattr(msg, 'content') and getattr(msg, 'type', '') == 'ai':
                        answer = msg.content
                        logger.info(f"Extracted answer from AI message: {answer[:100]}...")
                        break
                    elif isinstance(msg, dict) and 'content' in msg and msg.get('role') == 'assistant':
                        answer = msg['content']
                        logger.info(f"Extracted answer from assistant message dict: {answer[:100]}...")
                        break
            
            if answer:
                logger.info(f"[{query_id}] Generated answer: {answer[:100]}...")
            else:
                logger.warning(f"[{query_id}] No answer found in result messages")
                workflow_logger.warning(f"[{query_id}] Query failed: No answer generated")
                answer = "I'm sorry, I wasn't able to process your query correctly."
            
            # Create result dict
            result = {
                "answer": answer,
                "output": answer,  # For backwards compatibility
                "query": question,
                "duration": time.time() - state["search_starttime"],
                "thinking": end_state.get("thinking_steps", []),
                "has_error": False
            }
            
            workflow_logger.info(f"[{query_id}] Query completed in {result['duration']:.2f} seconds")
        except Exception as e:
            logger.error(f"Error in agent execution: {e}", exc_info=True)
            result = {
                "answer": f"I'm sorry, but an error occurred: {str(e)}",
                "output": f"I'm sorry, but an error occurred: {str(e)}",
                "query": question,
                "duration": time.time() - state["search_starttime"],
                "thinking": state.get("thinking_steps", []),
                "has_error": True
            }
            workflow_logger.error(f"[{query_id}] Query failed with error: {e}")
        
        return result

def create_prompt_for_llm(query: str, documents: List[Document]) -> str:
    """Create a prompt for the LLM based on the query and retrieved documents."""
    # Define maximum content length per document to keep prompts manageable
    MAX_DOCUMENT_CONTENT_LENGTH = 800  # Characters per document
    MAX_TOTAL_DOCUMENT_LENGTH = 6000   # Total characters for all documents
    
    # Format documents with limited content length
    formatted_docs = []
    total_length = 0
    
    for i, doc in enumerate(documents):
        # Get content and metadata
        content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
        
        # Limit content length for each document
        if len(content) > MAX_DOCUMENT_CONTENT_LENGTH:
            content = content[:MAX_DOCUMENT_CONTENT_LENGTH] + "..."
        
        # Get source if available
        source = ""
        if hasattr(doc, 'metadata'):
            source = doc.metadata.get('source', '')
        
        # Format document with source if available
        if source:
            formatted_doc = f"Document {i+1} [Source: {source}]:\n{content}\n\n"
        else:
            formatted_doc = f"Document {i+1}:\n{content}\n\n"
        
        # Check if adding this document would exceed our total limit
        if total_length + len(formatted_doc) <= MAX_TOTAL_DOCUMENT_LENGTH:
            formatted_docs.append(formatted_doc)
            total_length += len(formatted_doc)
        else:
            # If we're going to exceed the limit, add a truncated version or skip
            remaining_length = MAX_TOTAL_DOCUMENT_LENGTH - total_length
            if remaining_length > 100:  # Only add if we can include meaningful content
                truncated_doc = formatted_doc[:remaining_length] + "..."
                formatted_docs.append(truncated_doc)
            # Add note about documents being truncated
            formatted_docs.append(f"Note: {len(documents) - (i+1)} more documents were retrieved but truncated to save space.")
            break
    
    # Combine documents
    documents_text = "\n".join(formatted_docs) if formatted_docs else "No relevant documents found."
    
    # Create system prompt
    system_prompt = f"""You are Kevin, a professional consultant for Canadian universities. You help potential students find information about programs, admissions, scholarships, campus life, and more.
    
Your goal is to provide accurate, helpful information based on the provided documents. If the documents don't contain the answer, you should say so rather than making up information. Always cite your sources when possible.

USER QUERY: {query}

RETRIEVED DOCUMENTS:
{documents_text}

INSTRUCTIONS:
1. Answer the query using ONLY the information in the documents above.
2. If the documents don't contain enough information to fully answer the query, acknowledge this and suggest what additional information might be helpful.
3. Be concise but comprehensive.
4. Format your answer in Markdown for readability.
5. Do not reference these instructions in your answer.
6. Do not make up information that is not in the documents.
"""
    
    return system_prompt

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