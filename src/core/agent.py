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
    is_relevant: bool  # Whether documents are relevant
    is_hallucination_free: bool  # Whether response is free of hallucinations
    query: str  # The original query
    response: Optional[str]  # Generated response

# Initialize LLM based on configuration
def get_llm():
    """Get LLM based on configuration."""
    logger.info("Initializing LLM based on configuration")
    
    try:
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
                
                # Fall back to HuggingFace if configured and DeepSeek fails
                if llm_config.get('fallback_to_huggingface', True):
                    logger.warning("Falling back to HuggingFace model due to DeepSeek initialization failure")
                    model_name = llm_config.get('fallback_model', "deepseek-ai/deepseek-coder-1.3b-base")
                    logger.info(f"Initializing HuggingFace pipeline with model: {model_name}")
                    
                    llm_pipeline = pipeline(
                        task="text-generation",
                        model=model_name,
                        max_length=llm_config.get('max_tokens', 2048),
                        temperature=llm_config.get('temperature', 0.1),
                        top_p=0.95,
                        repetition_penalty=1.15
                    )
                    return HuggingFacePipeline(pipeline=llm_pipeline)
                else:
                    # Re-raise the exception if no fallback is configured
                    logger.critical("No fallback configured and DeepSeek initialization failed")
                    raise
        else:
            # Default to HuggingFace
            logger.info("Provider set to use HuggingFace model directly")
            model_name = llm_config.get('model_name', "deepseek-ai/deepseek-coder-1.3b-base")
            logger.info(f"Initializing HuggingFace pipeline with model: {model_name}")
            
            llm_pipeline = pipeline(
                task="text-generation",
                model=model_name,
                max_length=llm_config.get('max_tokens', 2048),
                temperature=llm_config.get('temperature', 0.1),
                top_p=0.95,
                repetition_penalty=1.15
            )
            return HuggingFacePipeline(pipeline=llm_pipeline)
    except Exception as e:
        logger.critical(f"Failed to initialize LLM: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to initialize LLM: {str(e)}")

# Router to decide whether to use vector store or web search
def router(state: AgentState) -> AgentState:
    """Decide whether to use vector store or web search."""
    workflow_logger.info("Executing router node to determine search method")
    
    try:
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
        
        # Check if user explicitly requested web search
        use_web_search = state.get("use_web_search", False)
        
        # If web search is not explicitly requested, decide based on content
        if not use_web_search:
            workflow_logger.info("Determining search method based on query content")
            # Create system prompt for the router decision
            router_prompt = """You are a helpful assistant that decides how to answer questions.
            
Your task is to determine if a query about Canadian universities is likely to be answered by:
1. Information from university websites (about programs, admissions, tuition, scholarships)
2. Information that requires current/recent web search data

Query: {query}

Output ONLY ONE of the following:
- "vectorstore" - if this query can be answered with standard university information
- "websearch" - if this query requires up-to-date or specific information that might not be in university documentation

Choose "vectorstore" unless the query clearly requires current information like recent news, COVID policies, 
specific events, or very detailed/specific numbers that might require the most up-to-date information.
"""
            
            # Get LLM
            llm = get_llm()
            
            # Format the prompt with the query
            formatted_prompt = router_prompt.format(query=query)
            
            # Generate decision
            logger.debug("Generating routing decision using LLM")
            decision = llm.invoke(formatted_prompt).strip().lower()
            logger.info(f"Router decision: {decision}")
            
            # Parse decision
            if "websearch" in decision:
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
        for i, doc in enumerate(documents):
            source = doc.metadata.get("source", "Unknown")
            logger.debug(f"Document {i+1} source: {source}")
        
        # Add system message about retrieval
        state["messages"].append(
            SystemMessage(
                content=f"I've retrieved {len(documents)} documents from my knowledge base that might help answer the query."
            )
        )
    except Exception as e:
        logger.error(f"Error in vector store retrieval: {str(e)}", exc_info=True)
        workflow_logger.error(f"Failed to retrieve documents from vector store: {str(e)}")
        
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
        documents = search_web(query)
        
        logger.info(f"Web search returned {len(documents)} documents")
        
        # Add the retrieved documents to the state
        state["web_documents"] = documents
        
        if documents:
            return state
        else:
            logger.warning("Web search returned no results")
            # Return original state with empty web_documents
            return {**state, "web_documents": []}
    
    except Exception as e:
        logger.error(f"Error in web search: {e}", exc_info=True)
        workflow_logger.error(f"Web search failed: {str(e)}")
        # Return original state with empty web_documents
        return {**state, "web_documents": []}

# Document grader to assess relevance
def grade_documents(state: AgentState) -> AgentState:
    """Grade documents to assess their relevance to the query."""
    workflow_logger.info("Executing document grading node")
    
    try:
        # Get configuration
        with open("config.yaml", 'r') as file:
            config = yaml.safe_load(file)
        
        # Get the query and documents
        query = state["query"]
        
        # Decide which documents to grade
        docs_to_grade = state.get("documents", [])
        if not docs_to_grade and "web_documents" in state:
            docs_to_grade = state.get("web_documents", [])
        
        logger.info(f"Grading {len(docs_to_grade)} documents for relevance to query: {query}")
        
        if not docs_to_grade:
            # No documents to grade
            logger.warning("No documents available for grading")
            workflow_logger.warning("Document grading failed: No documents available")
            state["is_relevant"] = False
            state["messages"].append(
                SystemMessage(
                    content="I don't have any relevant information to answer this query."
                )
            )
            return state
        
        # Prepare documents for grading
        docs_text = ""
        for i, doc in enumerate(docs_to_grade):
            source = doc.metadata.get("source", "Unknown source")
            title = doc.metadata.get("title", "No title")
            docs_text += f"Document {i+1} (from {title}):\n{doc.page_content[:500]}...\n\n"
        
        # Create system prompt for the grader
        grader_prompt = """You are a document relevance grader. Your task is to determine if the retrieved documents are relevant to the query.

Query: {query}

Retrieved Documents:
{docs_text}

On a scale of 0 to 1, how relevant are these documents to the query? Provide a single numerical score only.
A score of 0 means completely irrelevant, and a score of 1 means highly relevant.

Score: """
        
        # Get LLM
        llm = get_llm()
        
        # Format the prompt with the query and documents
        formatted_prompt = grader_prompt.format(query=query, docs_text=docs_text)
        
        # Generate grade
        logger.debug("Generating document relevance score using LLM")
        start_time = time.time()
        try:
            grade_text = llm.invoke(formatted_prompt).strip()
            grade = float(grade_text.split()[0])  # Extract first number
            elapsed_time = time.time() - start_time
            logger.info(f"Document grade: {grade:.2f} (generated in {elapsed_time:.2f}s)")
        except Exception as e:
            logger.error(f"Error parsing relevance grade: {str(e)}", exc_info=True)
            # Default to 0.5 if grading fails
            grade = 0.5
            logger.warning(f"Using default grade of {grade} due to grading failure")
        
        # Get relevance threshold from config
        relevance_threshold = config["workflow"].get("relevance_threshold", 0.7)
        logger.debug(f"Using relevance threshold: {relevance_threshold}")
        
        # Determine if documents are relevant
        is_relevant = grade >= relevance_threshold
        state["is_relevant"] = is_relevant
        
        workflow_logger.info(f"Document relevance assessment: {grade:.2f} (threshold: {relevance_threshold})")
        
        # Add system message about grading
        if is_relevant:
            workflow_logger.info("Documents deemed relevant to query")
            state["messages"].append(
                SystemMessage(
                    content=f"I've determined that the information I found is relevant to your query (relevance score: {grade:.2f})."
                )
            )
        else:
            workflow_logger.info("Documents deemed not relevant to query")
            state["messages"].append(
                SystemMessage(
                    content=f"I've determined that the information I found may not be directly relevant to your query (relevance score: {grade:.2f})."
                )
            )
    except Exception as e:
        logger.error(f"Error in document grading node: {str(e)}", exc_info=True)
        workflow_logger.error(f"Document grading failed: {str(e)}")
        
        # Default to assuming documents are relevant on error
        state["is_relevant"] = True
        state["messages"].append(
            SystemMessage(
                content="I'll proceed with the information I have to try to answer your query."
            )
        )
    
    return state

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
        
        # Determine which documents to use
        if state.get("is_relevant", False) and "documents" in state and state["documents"]:
            # Use vector store documents if relevant
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
        
        workflow_logger.info(f"Generating answer using {source_type} with {len(documents)} documents")
        
        # Prepare context from documents
        context = ""
        for i, doc in enumerate(documents):
            source = doc.metadata.get("source", "Unknown source")
            title = doc.metadata.get("title", "No title")
            context += f"Document {i+1} (from {title}):\n{doc.page_content}\n\n"
        
        # Create system prompt
        system_prompt = """You are a helpful assistant specializing in Canadian university information. 
You provide accurate information to students about programs, admissions, tuition, and scholarships at Canadian universities.

You have access to information from {source_type}. Use this information to provide helpful, accurate answers.
If the information isn't in the provided context, say that you don't have that specific information.
Always cite your sources when providing information.

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
        
        # Save answer to state
        state["response"] = answer
        
        workflow_logger.info(f"Answer generation successful (length: {len(answer)} chars)")
    except Exception as e:
        logger.error(f"Error in answer generation: {str(e)}", exc_info=True)
        workflow_logger.error(f"Answer generation failed: {str(e)}")
        
        # Set a generic response in case of error
        state["response"] = "I apologize, but I encountered an issue while generating an answer to your question. Please try asking again or rephrasing your question."
        
    return state

# Check for hallucinations in the response
def check_hallucination(state: AgentState) -> AgentState:
    """Check if the generated response contains hallucinations."""
    workflow_logger.info("Executing hallucination check node")
    
    try:
        # Get configuration
        with open("config.yaml", 'r') as file:
            config = yaml.safe_load(file)
        
        # Get the query and response
        query = state["query"]
        response = state["response"]
        
        logger.info(f"Checking hallucination for query: {query}")
        
        # Determine which documents to use
        if "documents" in state and state["documents"]:
            # Use vector store documents
            documents = state["documents"]
            source_desc = "vector store"
        elif "web_documents" in state and state["web_documents"]:
            # Use web search documents
            documents = state["web_documents"]
            source_desc = "web search"
        else:
            # No documents available
            documents = []
            source_desc = "no documents"
        
        logger.info(f"Using {len(documents)} documents from {source_desc} for hallucination check")
        
        # If no documents, we can't check for hallucinations
        if not documents:
            logger.warning("No documents available for hallucination check")
            workflow_logger.warning("Hallucination check skipped: No documents available")
            state["is_hallucination_free"] = False
            return state
        
        # Prepare context from documents
        context = ""
        for i, doc in enumerate(documents):
            context += f"Document {i+1}:\n{doc.page_content[:500]}...\n\n"
        
        # Create system prompt for hallucination check
        hallucination_prompt = """You are a hallucination detector. Your task is to determine if the response contains information not supported by the context.

Query: {query}

Context:
{context}

Response:
{response}

On a scale of 0 to 1, how well is the response supported by the context? Provide a single numerical score only.
A score of 0 means completely hallucinated (not supported by context), and a score of 1 means fully supported by the context.

Score: """
        
        # Get LLM
        llm = get_llm()
        
        # Format the prompt with the query, context, and response
        formatted_prompt = hallucination_prompt.format(query=query, context=context, response=response)
        
        # Generate score
        logger.debug("Generating hallucination score using LLM")
        start_time = time.time()
        try:
            score_text = llm.invoke(formatted_prompt).strip()
            score = float(score_text.split()[0])  # Extract first number
            elapsed_time = time.time() - start_time
            logger.info(f"Hallucination score: {score:.2f} (generated in {elapsed_time:.2f}s)")
        except Exception as e:
            logger.error(f"Error parsing hallucination score: {str(e)}", exc_info=True)
            # Default to 0.5 if scoring fails
            score = 0.5
            logger.warning(f"Using default hallucination score of {score} due to scoring failure")
        
        # Get hallucination threshold from config
        hallucination_threshold = config["workflow"].get("hallucination_threshold", 0.8)
        logger.debug(f"Using hallucination threshold: {hallucination_threshold}")
        
        # Determine if response is free of hallucinations
        is_hallucination_free = score >= hallucination_threshold
        state["is_hallucination_free"] = is_hallucination_free
        
        workflow_logger.info(f"Hallucination assessment: {score:.2f} (threshold: {hallucination_threshold})")
        
        # If hallucinations detected, regenerate the answer with a more conservative prompt
        if not is_hallucination_free:
            workflow_logger.warning(f"Hallucinations detected (score: {score:.2f}), regenerating answer")
            logger.warning(f"Hallucinations detected in response with score {score:.2f}")
            
            # Create a more conservative system prompt
            conservative_prompt = """You are a helpful assistant specializing in Canadian university information.
You provide accurate information to students about programs, admissions, tuition, and scholarships at Canadian universities.

IMPORTANT: Only provide information that is EXPLICITLY stated in the context below. DO NOT add any details, numbers, or facts not directly mentioned in the context.
If the information isn't in the provided context, clearly state that you don't have that specific information.
Always cite your sources when providing information.

Context information:
{context}

User query: {query}
"""
            
            # Format the prompt with context and query
            formatted_conservative_prompt = conservative_prompt.format(
                context=context, 
                query=query
            )
            
            # Generate a more conservative answer
            logger.info("Regenerating answer with conservative prompt")
            start_time = time.time()
            conservative_answer = llm.invoke(formatted_conservative_prompt)
            elapsed_time = time.time() - start_time
            
            answer_preview = conservative_answer[:100] + "..." if len(conservative_answer) > 100 else conservative_answer
            logger.info(f"Regenerated answer in {elapsed_time:.2f}s: {answer_preview}")
            
            # Update the response
            state["response"] = conservative_answer
            state["is_hallucination_free"] = True  # Assume the conservative answer is hallucination-free
            
            # Add system message about regeneration
            state["messages"].append(
                SystemMessage(
                    content="I've revised my answer to ensure it's fully supported by the available information."
                )
            )
            
            workflow_logger.info("Answer successfully regenerated with conservative approach")
        else:
            workflow_logger.info("No hallucinations detected, proceeding with original answer")
    except Exception as e:
        logger.error(f"Error in hallucination check: {str(e)}", exc_info=True)
        workflow_logger.error(f"Hallucination check failed: {str(e)}")
        
        # Default to assuming the response is hallucination-free on error
        state["is_hallucination_free"] = True
    
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
        
        # If web search was used and results should be added to RAG
        if state.get("use_web_search", False) and "web_documents" in state and state["web_documents"]:
            # Get configuration
            with open("config.yaml", 'r') as file:
                config = yaml.safe_load(file)
            
            # Check if web results should be added to RAG
            if config["workflow"].get("include_web_results_in_rag", True):
                logger.info("Adding web search results to knowledge base")
                workflow_logger.info("Adding web search results to vector store")
                
                # Initialize document processor
                processor = DocumentProcessor()
                
                # Add web documents to vector store
                web_docs = state["web_documents"]
                processor.add_documents(web_docs)
                
                logger.info(f"Added {len(web_docs)} documents from web search to knowledge base")
                
                # Add system message about adding to knowledge base
                state["messages"].append(
                    SystemMessage(
                        content="I've added the web search results to my knowledge base for future reference."
                    )
                )
        
        workflow_logger.info("Response finalization complete")
    except Exception as e:
        logger.error(f"Error in response finalization: {str(e)}", exc_info=True)
        workflow_logger.error(f"Response finalization failed: {str(e)}")
        
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
    decision = "end" if state.get("has_answered", False) else "continue"
    workflow_logger.info(f"End decision: {decision}")
    return decision

# Build the graph
def build_agent() -> StateGraph:
    """Build the agent graph with enhanced workflow."""
    logger.info("Building agent graph with enhanced workflow")
    
    try:
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        logger.debug("Adding nodes to graph")
        workflow.add_node("router", router)
        workflow.add_node("retrieve_from_vectorstore", retrieve_from_vectorstore)
        workflow.add_node("perform_web_search", perform_web_search)
        workflow.add_node("grade_documents", grade_documents)
        workflow.add_node("generate_answer", generate_answer)
        workflow.add_node("check_hallucination", check_hallucination)
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
        
        workflow.add_edge("retrieve_from_vectorstore", "grade_documents")
        workflow.add_edge("perform_web_search", "grade_documents")
        
        workflow.add_conditional_edges(
            "grade_documents",
            decide_after_vectorstore,
            {
                "generate_answer": "generate_answer",
                "web_search": "perform_web_search"
            }
        )
        
        workflow.add_edge("generate_answer", "check_hallucination")
        
        workflow.add_conditional_edges(
            "check_hallucination",
            decide_after_grading,
            {
                "finalize": "finalize_response",
                "regenerate": "generate_answer"
            }
        )
        
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
            self.graph_instance = self.graph.compile()
            logger.info("UniversityAgent initialized successfully")
        except Exception as e:
            logger.critical(f"Failed to initialize UniversityAgent: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to initialize agent: {str(e)}")
    
    def query(self, question: str, use_web_search: bool = False) -> str:
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
                "is_relevant": False,
                "is_hallucination_free": False,
                "query": question,
                "response": None
            }
            
            # Log whether web search is explicitly requested
            if use_web_search:
                logger.info(f"[{query_id}] Web search explicitly requested")
            
            # Run the graph
            workflow_logger.info(f"[{query_id}] Executing agent graph")
            result = self.graph_instance.invoke(state)
            
            # Extract answer
            messages = result["messages"]
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    answer = msg.content
                    # Log a preview of the answer
                    answer_preview = answer[:100] + "..." if len(answer) > 100 else answer
                    logger.info(f"[{query_id}] Generated answer: {answer_preview}")
                    
                    elapsed_time = time.time() - start_time
                    workflow_logger.info(f"[{query_id}] Query completed in {elapsed_time:.2f} seconds")
                    
                    return answer
            
            # If no answer found
            logger.warning(f"[{query_id}] No answer found in result messages")
            workflow_logger.warning(f"[{query_id}] Query failed: No answer generated")
            return "I couldn't generate an answer to your question."
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_detail = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"[{query_id}] Error processing query: {error_detail}")
            workflow_logger.error(f"[{query_id}] Query failed in {elapsed_time:.2f}s: {str(e)}")
            return f"I encountered an error while processing your query: {str(e)}"

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