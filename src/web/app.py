"""
Streamlit app for Canadian University Information Agent.
"""

import os
import sys
import yaml
import time
import traceback
import streamlit as st
from streamlit_chat import message
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import project modules
from src.core.agent import UniversityAgent
from src.data.scraper import WebScraper
from src.core.document_processor import DocumentProcessor
from src.utils.logger import get_logger, set_log_level, workflow_logger

# Configure module logger
logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Canadian University Information Assistant",
    page_icon="🎓",
    layout="wide"
)

# Load configuration for logging
def load_config():
    """Load configuration from config.yaml."""
    try:
        with open("config.yaml", 'r') as file:
            config = yaml.safe_load(file)
            logger.debug("Configuration loaded successfully")
            return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}", exc_info=True)
        # Return a default configuration
        return {
            "workflow": {
                "include_web_results_in_rag": True,
                "relevance_threshold": 0.7,
                "hallucination_threshold": 0.8
            },
            "web_search": {
                "enabled": True
            },
            "universities": []
        }

logger.info("Starting Canadian University Information Assistant app")

# Initialize session state variables
if "messages" not in st.session_state:
    logger.debug("Initializing message history")
    st.session_state.messages = []

if "agent" not in st.session_state:
    logger.info("Initializing University Agent")
    try:
        st.session_state.agent = UniversityAgent()
        logger.info("University Agent initialized successfully")
    except Exception as e:
        logger.critical(f"Failed to initialize University Agent: {e}", exc_info=True)
        st.error(f"Failed to initialize the agent: {str(e)}")

if "config" not in st.session_state:
    logger.info("Loading configuration")
    st.session_state.config = load_config()

if "use_web_search" not in st.session_state:
    st.session_state.use_web_search = False

if "show_workflow" not in st.session_state:
    st.session_state.show_workflow = False

# Page header
st.header("🎓 Canadian University Information Assistant")
st.markdown("Ask questions about programs, admissions, tuition, and scholarships at Canadian universities.")

# Main layout with two columns
col1, col2 = st.columns([2, 1])

# Main chat interface in the first column
with col1:
    st.subheader("Chat with the University Assistant")
    
    # Toggle for web search
    previous_web_search = st.session_state.use_web_search
    st.session_state.use_web_search = st.toggle(
        "Enable web search for up-to-date information",
        value=st.session_state.use_web_search,
        help="When enabled, the assistant can search the web for information not in its knowledge base"
    )
    
    # Log if web search setting changed
    if previous_web_search != st.session_state.use_web_search:
        logger.info(f"Web search setting changed to: {st.session_state.use_web_search}")
    
    # Toggle for showing workflow details
    previous_workflow = st.session_state.show_workflow
    st.session_state.show_workflow = st.toggle(
        "Show workflow details",
        value=st.session_state.show_workflow,
        help="When enabled, shows the reasoning process used by the assistant"
    )
    
    # Log if workflow detail setting changed
    if previous_workflow != st.session_state.show_workflow:
        logger.info(f"Workflow details setting changed to: {st.session_state.show_workflow}")
    
    # Display chat messages
    message_container = st.container()
    with message_container:
        for i, (role, content) in enumerate(st.session_state.messages):
            if role == "user":
                message(content, is_user=True, key=f"{i}_user")
            elif role == "assistant":
                message(content, is_user=False, key=f"{i}_assistant")
            elif role == "system" and st.session_state.show_workflow:
                # Only show system messages (workflow details) if enabled
                st.info(content)
    
    # Chat input
    user_query = st.chat_input("Ask about Canadian universities...")
    
    if user_query:
        # Add user message to chat
        logger.info(f"User query: {user_query}")
        st.session_state.messages.append(("user", user_query))
        message(user_query, is_user=True, key=f"{len(st.session_state.messages)}_user")
        
        # Get agent response
        with st.spinner("Thinking..."):
            try:
                query_id = f"query_{int(time.time())}"
                logger.info(f"[{query_id}] Processing query with web_search={st.session_state.use_web_search}")
                workflow_logger.info(f"[{query_id}] Web interface query: {user_query}")
                
                start_time = time.time()
                
                # Call agent with web search flag
                response = st.session_state.agent.query(
                    user_query,
                    use_web_search=st.session_state.use_web_search
                )
                
                elapsed_time = time.time() - start_time
                logger.info(f"[{query_id}] Query processed in {elapsed_time:.2f} seconds")
                
                # Add assistant message to chat
                st.session_state.messages.append(("assistant", response))
                message(response, is_user=False, key=f"{len(st.session_state.messages)}_assistant")
                
                # If web search was used and should be added to RAG
                if st.session_state.use_web_search and st.session_state.config["workflow"].get("include_web_results_in_rag", True):
                    # This is handled by the agent now, but we can show a message
                    if st.session_state.show_workflow:
                        st.success("Web search results have been added to the knowledge base for future reference.")
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                error_details = traceback.format_exc()
                logger.error(f"Error processing query: {str(e)}\n{error_details}")
                workflow_logger.error(f"Query failed: {str(e)}")
                
                st.session_state.messages.append(("assistant", error_msg))
                message(error_msg, is_user=False, key=f"{len(st.session_state.messages)}_assistant")
    
    # Add sample questions
    st.markdown("---")
    st.subheader("Sample Questions")
    
    sample_questions = [
        "What are the admission requirements for international students at UBC?",
        "How much is tuition for a Computer Science degree at University of Toronto?",
        "What scholarships are available for graduate students at McGill University?",
        "What programs does the University of Alberta offer in Engineering?",
        "When are the application deadlines for Fall 2023 admission at Canadian universities?"
    ]
    
    current_questions = sample_questions[:3]
    more_questions = sample_questions[3:]
    
    # First row of sample questions
    cols = st.columns(len(current_questions))
    for i, col in enumerate(cols):
        if col.button(current_questions[i], key=f"sample_{i}"):
            # Simulate clicking the question
            logger.info(f"Sample question selected: {current_questions[i]}")
            st.session_state.messages.append(("user", current_questions[i]))
            st.rerun()
    
    # Second row of sample questions and a web search example
    cols = st.columns(len(more_questions) + 1)
    for i, col in enumerate(cols[:-1]):
        if col.button(more_questions[i], key=f"sample_{i+len(current_questions)}"):
            # Simulate clicking the question
            logger.info(f"Sample question selected: {more_questions[i]}")
            st.session_state.messages.append(("user", more_questions[i]))
            st.rerun()
    
    # Add a web search sample question
    if cols[-1].button("What are the latest COVID-19 policies for McGill University?", key="web_sample"):
        # For this question, ensure web search is enabled
        logger.info("Web search sample question selected with web search enabled")
        st.session_state.use_web_search = True
        st.session_state.messages.append(("user", "What are the latest COVID-19 policies for McGill University?"))
        st.rerun()

# Sidebar for configuration and data management
with st.sidebar:
    st.header("Data Management")
    st.write("Use these tools to manage the scraped data.")
    
    # Data collection section
    st.subheader("Web Scraping")
    if st.button("Scrape University Websites"):
        logger.info("Web scraping initiated from UI")
        workflow_logger.info("Starting web scraping operation")
        
        with st.spinner("Scraping university websites. This may take several minutes..."):
            try:
                start_time = time.time()
                scraper = WebScraper()
                documents = scraper.scrape_all_universities()
                
                if documents:
                    logger.info(f"Successfully scraped {len(documents)} pages from university websites")
                    processor = DocumentProcessor()
                    processor.add_documents(documents)
                    elapsed_time = time.time() - start_time
                    logger.info(f"Scraped and processed {len(documents)} documents in {elapsed_time:.2f} seconds")
                    workflow_logger.info(f"Web scraping complete: {len(documents)} documents added to knowledge base")
                    st.success(f"Successfully scraped {len(documents)} pages from university websites!")
                else:
                    logger.warning("No documents were scraped from university websites")
                    workflow_logger.warning("Web scraping operation returned no documents")
                    st.error("Failed to scrape any data from university websites.")
            except Exception as e:
                error_details = traceback.format_exc()
                logger.error(f"Error during web scraping: {str(e)}\n{error_details}")
                workflow_logger.error(f"Web scraping failed: {str(e)}")
                st.error(f"Error during web scraping: {str(e)}")
    
    # Add logging controls
    st.subheader("Logging Controls")
    log_level = st.selectbox(
        "Log Level",
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        index=1  # Default to INFO
    )
    
    if st.button("Update Log Level"):
        logger.info(f"Setting log level to {log_level}")
        # Set log level
        numeric_level = getattr(logging, log_level)
        set_log_level(numeric_level)
        st.success(f"Log level set to {log_level}")
    
    # Show configuration
    st.subheader("Current Configuration")
    
    # Display universities
    with st.expander("Universities"):
        universities = st.session_state.config.get("universities", [])
        university_names = [u.get("name") for u in universities]
        for name in university_names:
            st.write(f"- {name}")
    
    # Display web search settings
    with st.expander("Web Search Settings"):
        web_search_enabled = st.session_state.config.get("web_search", {}).get("enabled", False)
        st.write(f"Web search enabled: {web_search_enabled}")
        
        include_in_rag = st.session_state.config.get("workflow", {}).get("include_web_results_in_rag", True)
        st.write(f"Include web results in RAG: {include_in_rag}")
    
    # About section
    st.subheader("About")
    st.markdown("""
    This application uses LangGraph to create a conversational agent that can:
    
    1. Scrape Canadian university websites
    2. Process and store information in a vector database
    3. Retrieve relevant information based on user queries
    4. Search the web for up-to-date information when needed
    5. Grade document relevance and check for hallucinations
    6. Generate helpful responses using DeepSeek R1 or alternative LLMs
    
    The system is designed to help prospective students find information about programs, admissions, tuition, and scholarships.
    """)

# Secondary column for current state
with col2:
    st.subheader("Agent Status")
    
    # Show search mode
    search_mode = "Web Search Enabled" if st.session_state.use_web_search else "Using Knowledge Base Only"
    st.write(f"**Current Mode:** {search_mode}")
    
    # Show workflow parameters
    with st.expander("Workflow Parameters"):
        relevance_threshold = st.session_state.config.get("workflow", {}).get("relevance_threshold", 0.7)
        st.write(f"Document relevance threshold: {relevance_threshold}")
        
        hallucination_threshold = st.session_state.config.get("workflow", {}).get("hallucination_threshold", 0.8)
        st.write(f"Hallucination threshold: {hallucination_threshold}")
    
    # Show workflow diagram or explanation
    with st.expander("Workflow Explanation"):
        st.markdown("""
        The agent follows this workflow:
        
        1. **Router** - Decides whether to search the knowledge base or the web
        2. **Retriever** - Gets relevant documents from the chosen source
        3. **Document Grader** - Assesses if the documents are relevant
        4. **Answer Generator** - Creates a response based on the documents
        5. **Hallucination Checker** - Ensures the response is factual
        6. **Response Finalizer** - Delivers the answer and updates the knowledge base
        
        If documents from the knowledge base aren't relevant, the agent will automatically search the web.
        """)
        
        # Simple workflow diagram
        st.graphviz_chart('''
        digraph {
            rankdir=TB;
            node [shape=box, style=filled, fillcolor=lightblue];
            
            Query -> Router;
            Router -> VectorStore [label="standard info"];
            Router -> WebSearch [label="current info"];
            VectorStore -> DocGrader;
            WebSearch -> DocGrader;
            DocGrader -> Generator [label="relevant"];
            DocGrader -> WebSearch [label="irrelevant"];
            Generator -> HallucinationCheck;
            HallucinationCheck -> Finalizer [label="factual"];
            HallucinationCheck -> Generator [label="needs revision"];
            Finalizer -> Response;
        }
        ''')

# Log app startup complete
logger.info("Application UI initialized successfully")

if __name__ == "__main__":
    pass 