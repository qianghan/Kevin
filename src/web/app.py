#!/usr/bin/env python3
"""
Streamlit web interface for Kevin.
"""

import os
import sys
import streamlit as st
from pathlib import Path
import time

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
    """Configure the Streamlit page appearance."""
    st.set_page_config(
        page_title="Kevin - University Information Agent",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better UI
    st.markdown("""
    <style>
    /* Improved chat interface styling */
    .chat-message {
        padding: 1.5rem; 
        border-radius: 0.8rem; 
        margin-bottom: 1rem; 
        display: flex;
    }
    
    .chat-message.user {
        background-color: #f0f2f6;
    }
    
    .chat-message.assistant {
        background-color: #e6f3ff;
    }
    
    .chat-message .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 1rem;
    }
    
    .chat-message .message {
        flex: 1;
    }
    
    /* Typing animation styling */
    @keyframes typing {
        0% { opacity: 0.3; }
        50% { opacity: 1; }
        100% { opacity: 0.3; }
    }
    
    .typing-indicator {
        display: flex;
        margin: 10px 0;
    }
    
    .typing-indicator span {
        height: 8px;
        width: 8px;
        background-color: #4CAF50;
        border-radius: 50%;
        margin: 0 2px;
        display: inline-block;
    }
    
    .typing-indicator span:nth-child(1) {
        animation: typing 1s infinite;
    }
    
    .typing-indicator span:nth-child(2) {
        animation: typing 1s infinite 0.2s;
    }
    
    .typing-indicator span:nth-child(3) {
        animation: typing 1s infinite 0.4s;
    }
    
    /* Thinking process styling */
    .thinking-timeline {
        border-left: 2px solid #ccc;
        padding-left: 20px;
        margin-left: 10px;
    }
    
    .thinking-step {
        position: relative;
        margin-bottom: 20px;
        padding-left: 10px;
    }
    
    .thinking-step:before {
        content: '';
        position: absolute;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #4CAF50;
        left: -27px;
        top: 5px;
    }
    
    .thinking-error:before {
        background: #f44336;
    }
    
    .thinking-time {
        color: #777;
        font-size: 0.8em;
    }
    
    .thinking-description {
        font-weight: bold;
    }
    
    .thinking-details {
        margin-top: 5px;
        padding: 10px;
        background: #f5f5f5;
        border-radius: 5px;
        font-size: 0.9em;
    }
    
    .search-highlight {
        background-color: #ffff99;
        padding: 0 3px;
        border-radius: 3px;
    }
    
    .error-highlight {
        color: #f44336;
        font-weight: bold;
    }
    
    .timing-highlight {
        color: #2196F3;
        font-weight: bold;
    }
    
    /* Animated typing effect */
    .typewriter {
        overflow: hidden;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    .typing-animation {
        display: inline-block;
        padding-right: 0.1em;
        border-right: 0.15em solid #4CAF50;
        animation: blink-caret 0.75s step-end infinite;
    }
    
    @keyframes blink-caret {
        from, to { border-color: transparent }
        50% { border-color: #4CAF50 }
    }
    
    /* Better source styling */
    .source-item {
        border: 1px solid #e6e6e6;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 15px;
        background-color: #fafafa;
    }
    
    .source-title {
        font-weight: bold;
        color: #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

    # JavaScript for simulating typing effect
    st.markdown("""
    <script>
    function simulateTyping(elementId, text, delay = 30) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        let i = 0;
        element.innerHTML = "";
        const intervalId = setInterval(() => {
            if (i < text.length) {
                element.innerHTML += text.charAt(i);
                i++;
            } else {
                clearInterval(intervalId);
                element.classList.remove("typing-animation");
            }
        }, delay);
    }
    </script>
    """, unsafe_allow_html=True)

# Mock agent class for fallback
class MockAgent:
    """Mock agent for testing or when dependencies are missing"""
    def __init__(self):
        """Initialize the mock agent"""
        logger.info("Initializing mock agent")
        
    def query(self, query_text, use_web_search=False):
        """Return a mock response"""
        logger.info(f"Mock agent received query: {query_text}")
        return {
            "output": f"I'm sorry, but the full agent couldn't be initialized correctly. The DeepSeek API might not be configured properly, or there might be an issue with dependencies. Here's what you asked: '{query_text}'",
            "thinking": [
                {"step": "mock_response", "time": time.strftime("%H:%M:%S"), "description": "Generated mock response"}
            ]
        }
                 
    def get_documents(self, query):
        """Return empty document list"""
        return []

# Placeholder for agent initialization with DeepSeek API
def initialize_agent(use_mock=False):
    """Initialize the Kevin agent with DeepSeek API only"""
    if use_mock:
        logger.info("Using mock agent")
        return MockAgent()
        
    # Ensure environment variable is set
    os.environ['USE_DEEPSEEK_ONLY'] = '1'
    
    try:
        # Try to import and initialize the real agent
        try:
            from src.core.agent_setup import initialize_agent as init_agent
            return init_agent()
        except RuntimeError as e:
            if "'utf-8' codec can't decode byte" in str(e):
                logger.error(f"Transformers library import error: {str(e)}")
                logger.error("This is likely due to an encoding issue with the transformers library.")
                st.error("""
                Could not initialize the agent due to a transformers library encoding issue.
                
                **Possible solutions:**
                1. Make sure your Python environment uses UTF-8 encoding
                2. Try reinstalling the transformers library with: `pip uninstall -y transformers && pip install transformers`
                3. Check if any of your Python files have non-UTF-8 characters
                """)
            else:
                logger.error(f"Failed to initialize agent: {str(e)}")
                st.error(f"Failed to initialize agent: {str(e)}")
            
            return initialize_agent(use_mock=True)
            
    except Exception as e:
        logger.error(f"Unexpected error initializing agent: {str(e)}", exc_info=True)
        st.error(f"Unexpected error initializing agent: {str(e)}")
        return MockAgent()

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
        show_thinking = st.checkbox("Show thinking process", value=True)
        typing_animation = st.checkbox("Enable typing animation", value=True)
        typing_speed = st.slider("Typing speed", min_value=10, max_value=100, value=40, 
                               help="Adjust speed of typing animation (higher = faster)")
        
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
            # Create a container for the thinking indicator
            thinking_indicator = st.empty()
            
            # Show thinking indicator
            if typing_animation:
                thinking_indicator.markdown("""
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                """, unsafe_allow_html=True)
            else:
                with thinking_indicator:
                    st.spinner("Kevin is thinking...")
            
            # Create a placeholder for the streamed response
            response_placeholder = st.empty()
            
            try:
                # Get response from agent
                response = st.session_state.agent.query(prompt, use_web_search=use_web_search)
                
                # Handle different response formats
                if isinstance(response, dict):
                    answer = response.get("output", response.get("answer", str(response)))
                    thinking_steps = response.get("thinking", [])
                else:
                    answer = str(response)
                    thinking_steps = []
                
                # Clear thinking indicator
                thinking_indicator.empty()
                
                # Display the answer with typing animation if enabled
                if typing_animation:
                    # Create a unique ID for this response
                    response_id = f"response-{hash(prompt)}-{int(time.time())}"
                    
                    # Create a container with the ID
                    response_placeholder.markdown(f'<div id="{response_id}" class="typewriter typing-animation"></div>', unsafe_allow_html=True)
                    
                    # Split the answer into chunks to simulate streaming
                    chunks = []
                    words = answer.split()
                    chunk_size = max(1, len(words) // 10)  # Aim for ~10 chunks
                    
                    for i in range(0, len(words), chunk_size):
                        chunk = " ".join(words[i:i+chunk_size])
                        chunks.append(chunk)
                    
                    # Stream each chunk
                    full_text = ""
                    for chunk in chunks:
                        full_text += chunk + " "
                        # Replace HTML elements to avoid breaking the rendering
                        safe_text = full_text.replace("<", "&lt;").replace(">", "&gt;")
                        response_placeholder.markdown(f'<div id="{response_id}" class="typewriter">{safe_text}</div>', unsafe_allow_html=True)
                        time.sleep(len(chunk) / typing_speed)  # Delay based on chunk length and typing speed
                else:
                    # Display the full answer immediately
                    response_placeholder.markdown(answer)
                
                # Store response
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # Show thinking process if enabled
                if show_thinking and thinking_steps:
                    with st.expander("Show Kevin's Thinking Process", expanded=True):
                        # Add a header with timing info
                        total_steps = len(thinking_steps)
                        start_time = thinking_steps[0].get("time", "") if thinking_steps else ""
                        end_time = thinking_steps[-1].get("time", "") if thinking_steps else ""
                        
                        if start_time and end_time:
                            st.markdown(f"**Processing Timeline:** {start_time} → {end_time} | **Steps:** {total_steps}")
                        
                        # Create a timeline view of the thinking steps
                        st.markdown('<div class="thinking-timeline">', unsafe_allow_html=True)
                        
                        for step in thinking_steps:
                            step_time = step.get("time", "")
                            step_name = step.get("description", step.get("step", "Unknown step"))
                            details = step.get("details", {})
                            
                            # Check if this is an error step to apply special styling
                            is_error = "error" in step.get("step", "").lower() or "fail" in step.get("step", "").lower()
                            step_class = "thinking-step thinking-error" if is_error else "thinking-step"
                            
                            # Format the step display using custom CSS
                            st.markdown(f'<div class="{step_class}">', unsafe_allow_html=True)
                            st.markdown(f'<span class="thinking-time">{step_time}</span> - <span class="thinking-description">{step_name}</span>', unsafe_allow_html=True)
                            
                            # Display details in a formatted way
                            if details:
                                st.markdown('<div class="thinking-details">', unsafe_allow_html=True)
                                
                                # Handle different types of details
                                for key, value in details.items():
                                    # Format key for better readability
                                    display_key = key.replace("_", " ").title()
                                    
                                    if isinstance(value, list) and len(value) > 0:
                                        st.markdown(f"<b>{display_key}:</b>", unsafe_allow_html=True)
                                        for item in value:
                                            if isinstance(item, dict):
                                                for k, v in item.items():
                                                    # Format dictionary item keys
                                                    display_k = k.replace("_", " ").title()
                                                    st.markdown(f"• {display_k}: <span class='search-highlight'>{v}</span>", unsafe_allow_html=True)
                                            else:
                                                st.markdown(f"• <span class='search-highlight'>{item}</span>", unsafe_allow_html=True)
                                    elif isinstance(value, dict):
                                        st.markdown(f"<b>{display_key}:</b>", unsafe_allow_html=True)
                                        for k, v in value.items():
                                            display_k = k.replace("_", " ").title()
                                            st.markdown(f"• {display_k}: {v}", unsafe_allow_html=True)
                                    elif key == "time_taken" or key == "elapsed_time":
                                        # Highlight timing information
                                        st.markdown(f"<b>{display_key}:</b> <span class='timing-highlight'>{value}</span>", unsafe_allow_html=True)
                                    elif key == "error":
                                        # Highlight errors
                                        st.markdown(f"<b>{display_key}:</b> <span class='error-highlight'>{value}</span>", unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"<b>{display_key}:</b> {value}", unsafe_allow_html=True)
                                
                                st.markdown('</div>', unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                
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