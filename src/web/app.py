#!/usr/bin/env python3
"""
Streamlit web interface for Kevin.
"""

import os
import sys
import streamlit as st
from pathlib import Path

# Fix for PyTorch/Streamlit compatibility issue
# Set environment variables before ANY imports that might use PyTorch
os.environ['TORCH_WARN_ONCE'] = '1'
os.environ['USE_DEEPSEEK_ONLY'] = '1'  # Custom flag to ensure only DeepSeek API is used

# Add parent directory to path if needed
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir.parent))

# Import utilities first (fewer dependencies)
try:
    from src.utils.logger import get_logger, set_log_level, workflow_logger, api_logger
    logger = get_logger(__name__)
    logger_available = True
except ImportError as e:
    logger_available = False
    print(f"Logger import error: {e}")

# Function to load config (separate to isolate errors)
def load_config():
    """Load configuration from config.yaml"""
    try:
        import yaml
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                # Ensure DeepSeek is used as provider and fallback is disabled
                if 'llm' in config:
                    config['llm']['provider'] = 'deepseek'
                    config['llm']['fallback_to_huggingface'] = False
                return config
        return {}
    except Exception as e:
        st.error(f"Error loading config: {e}")
        return {}

# Set up the Streamlit page
def setup_page():
    """Configure the Streamlit page settings"""
    st.set_page_config(
        page_title="Kevin - University Information Agent",
        page_icon="🎓",
        layout="wide"
    )
    
    # Add custom CSS
    st.markdown("""
    <style>
    .main {
        padding: 20px;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    </style>
    """, unsafe_allow_html=True)

# Placeholder for agent initialization with DeepSeek API
def initialize_agent(use_mock=False):
    """Initialize the Kevin agent with DeepSeek API only"""
    if use_mock:
        # Create a mock agent for testing or when dependencies are missing
        class MockAgent:
            def query(self, query_text, use_web_search=False):
                return f"Mock response to: {query_text} (DeepSeek API not initialized correctly)"
                
            def get_documents(self, query):
                return []
        
        return MockAgent()
    
    # Try to import and initialize the real agent
    try:
        # First, ensure DeepSeekAPI is correctly initialized
        from src.models.deepseek_client import DeepSeekAPI
        
        # Test DeepSeekAPI initialization
        try:
            # Test create API client
            api_client = DeepSeekAPI()
            if logger_available:
                logger.info(f"Successfully initialized DeepSeekAPI with model: {api_client.model_name}")
                api_logger.info(f"DeepSeekAPI initialized with model: {api_client.model_name}")
        except Exception as e:
            if logger_available:
                logger.error(f"Failed to initialize DeepSeekAPI: {str(e)}")
            raise
        
        # Now import the agent
        try:
            from src.core.agent_setup import initialize_agent as init_agent
            return init_agent()
        except ImportError:
            # Try alternative import
            from src.core.agent import Kevin
            return Kevin()
    except Exception as e:
        if logger_available:
            logger.error(f"Failed to initialize agent: {str(e)}")
        st.error(f"Failed to initialize agent: {str(e)}")
        st.warning("Using mock agent instead. Please ensure DeepSeek API is configured correctly.")
        return initialize_agent(use_mock=True)

# Main UI function
def main():
    """Main function for the Streamlit app."""
    setup_page()
    
    # Load configuration
    config = load_config()
    
    # Set up logging if available
    if logger_available:
        set_log_level("INFO")
        logger.info("Starting Kevin web interface")
    
    # Sidebar
    with st.sidebar:
        st.title("Kevin 🎓")
        st.markdown("### Canadian University Information Agent")
        
        # Toggle for web search
        use_web_search = st.checkbox("Enable web search", value=False)
        
        # Settings
        st.markdown("### Settings")
        show_sources = st.checkbox("Show sources", value=True)
        
        # About
        st.markdown("---")
        st.markdown("### About")
        st.markdown("Kevin is an AI-powered agent that provides information about Canadian universities.")
        
        # API Status
        if 'agent' in st.session_state and hasattr(st.session_state.agent, 'model_name'):
            st.markdown("---")
            st.markdown(f"**API Status**: Connected to DeepSeek API")
            st.markdown(f"**Model**: {getattr(st.session_state.agent, 'model_name', 'deepseek-chat')}")
        
        # Reset button
        if st.button("Reset Conversation"):
            st.session_state.messages = []
            st.session_state.documents = []
            st.rerun()
    
    # Main content
    st.title("Kevin - University Information Agent 🎓")
    st.markdown("""
    Ask me about Canadian universities - admissions, programs, tuition, scholarships, and more!
    """)
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Initialize document store
    if "documents" not in st.session_state:
        st.session_state.documents = []
    
    # Initialize agent immediately (no lazy loading)
    # This avoids the PyTorch initialization issue during Streamlit's hot-reloading
    if "agent" not in st.session_state:
        st.session_state.agent = initialize_agent(use_mock=False)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about Canadian universities..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Get response from agent
                    response = st.session_state.agent.query(prompt, use_web_search=use_web_search)
                    
                    # Handle different response formats
                    if isinstance(response, dict):
                        answer = response.get("output", response.get("answer", str(response)))
                    else:
                        answer = str(response)
                    
                    st.write(answer)
                    
                    # Store response
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    
                    # Show sources if enabled
                    if show_sources:
                        try:
                            # Try to get documents from agent
                            documents = st.session_state.agent.get_documents(prompt) 
                            if documents:
                                with st.expander("Sources"):
                                    for i, doc in enumerate(documents):
                                        st.markdown(f"**Source {i+1}**: {doc.metadata.get('source', 'Unknown')}")
                                        st.markdown(doc.page_content)
                                        st.markdown("---")
                        except Exception as e:
                            # Quietly fail if we can't get documents
                            pass
                            
                except Exception as e:
                    error_msg = f"Error generating response: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    if logger_available:
                        logger.error(error_msg)

def run_app():
    """Entry point for the application."""
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.markdown("Please try reloading the page. If the problem persists, check the logs.")
        if logger_available:
            logger.error(f"Application error: {e}", exc_info=True)

# Run the app
if __name__ == "__main__":
    run_app() 