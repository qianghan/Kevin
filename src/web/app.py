#!/usr/bin/env python3
"""
Streamlit web interface for Kevin.
"""

import os
import sys
import streamlit as st
from pathlib import Path
import time
import random
import re
import queue
import threading

# Fix for PyTorch/Streamlit compatibility issue
# Set environment variables before ANY imports that might use PyTorch
os.environ['TORCH_WARN_ONCE'] = '1'
os.environ['USE_DEEPSEEK_ONLY'] = '1'  # Custom flag to ensure only DeepSeek API is used

# Add parent directory to path if needed
current_dir = Path(__file__).parent
src_dir = current_dir.parent
project_root = src_dir.parent
for path_to_add in [str(src_dir), str(project_root)]:
    if path_to_add not in sys.path:
        sys.path.append(path_to_add)
        print(f"Added {path_to_add} to sys.path")

# Import utilities first (fewer dependencies)
try:
    from utils.logger import get_logger, set_log_level, workflow_logger, api_logger
    logger = get_logger(__name__)
    logger_available = True
except ImportError as e:
    print(f"First logger import error: {e}")
    try:
        from src.utils.logger import get_logger, set_log_level, workflow_logger, api_logger
        logger = get_logger(__name__)
        logger_available = True
    except ImportError as e:
        logger_available = False
        print(f"Second logger import error: {e}")

# Global variables for thread communication
thinking_steps_lock = threading.Lock()
latest_thinking_steps = []
thinking_thread_active = False
stop_thinking_thread = threading.Event()
last_update_time = 0  # Track when we last updated the thinking steps display

# Function to safely update thinking steps without session state
def update_global_thinking_steps(agent):
    """Safely update global thinking steps from agent instance"""
    global latest_thinking_steps
    if agent and hasattr(agent, 'latest_thinking_steps'):
        steps = getattr(agent, 'latest_thinking_steps', [])
        if steps:
            with thinking_steps_lock:
                latest_thinking_steps = steps.copy() if steps else []
    return latest_thinking_steps

# Function to poll thinking steps without using Streamlit context
def poll_thinking_steps_safe(agent_ref, stop_event):
    """Thread-safe background polling that doesn't use Streamlit context"""
    global latest_thinking_steps
    
    # Wait a moment for everything to initialize
    time.sleep(0.5)
    
    while not stop_event.is_set():
        try:
            # Get the agent from the reference (not from session state)
            if agent_ref and hasattr(agent_ref, 'latest_thinking_steps'):
                steps = getattr(agent_ref, 'latest_thinking_steps', [])
                if steps:
                    with thinking_steps_lock:
                        # Only update if we have new steps or more steps
                        if (not latest_thinking_steps) or len(steps) > len(latest_thinking_steps):
                            latest_thinking_steps = steps.copy()
        except Exception as e:
            # Just continue on error
            pass
            
        # Sleep for a short time before checking again
        time.sleep(0.2)  # Poll every 200ms

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

# Function to initialize agent, in a separate function to isolate errors
def initialize_agent(use_mock=False):
    """Initialize agent interface"""
    if use_mock:
        # Return a simple mock for testing
        try:
            from utils.mock import MockAgent
            return MockAgent()
        except ImportError:
            # If utils.mock import fails, try with src.utils.mock
            try:
                from src.utils.mock import MockAgent
                return MockAgent()
            except ImportError:
                # If both imports fail, use inline MockAgent class
                class MockAgent:
                    """Mock agent for testing or when dependencies are missing"""
                    def __init__(self):
                        """Initialize the mock agent"""
                        if logger_available:
                            logger.info("Initializing mock agent")
                        
                    def query(self, query_text, use_web_search=False):
                        """Return a mock response"""
                        if logger_available:
                            logger.info(f"Mock agent received query: {query_text}")
                        return {
                            "output": f"I'm sorry, but the full agent couldn't be initialized correctly. Here's what you asked: '{query_text}'",
                            "thinking": [
                                {"type": "mock_response", "description": "Generated mock response", "duration_ms": 100, "content": "Mock thinking process"}
                            ]
                        }
                        
                    def get_documents(self, query):
                        """Return empty document list"""
                        return []
                
                return MockAgent()
    
    try:
        # Try with correct class name UniversityAgent
        try:
            from src.core.agent import UniversityAgent
            agent = UniversityAgent()
            if logger_available:
                logger.info("Agent initialized successfully")
            return agent
        except (ImportError, AttributeError) as e:
            # Try alternative import approach
            if logger_available:
                logger.warning(f"First import attempt failed: {e}, trying alternative import")
            
            # Try importing from agent_setup
            try:
                from src.core.agent_setup import initialize_agent as init_agent
                return init_agent()
            except (ImportError, AttributeError) as e:
                if logger_available:
                    logger.error(f"Failed to initialize agent from agent_setup: {e}")
                raise
    except Exception as e:
        if logger_available:
            logger.error(f"Failed to initialize agent: {e}")
        st.error(f"Failed to initialize agent: {e}")
        
        # Try to import MockAgent from utils.mock
        try:
            from utils.mock import MockAgent
            return MockAgent()
        except ImportError:
            # Try with src prefix
            try:
                from src.utils.mock import MockAgent
                return MockAgent()
            except ImportError:
                # Fall back to inline definition if imports fail
                class MockAgent:
                    """Mock agent for testing or when dependencies are missing"""
                    def __init__(self):
                        """Initialize the mock agent"""
                        if logger_available:
                            logger.info("Initializing mock agent")
                        
                    def query(self, query_text, use_web_search=False):
                        """Return a mock response"""
                        if logger_available:
                            logger.info(f"Mock agent received query: {query_text}")
                        return {
                            "output": f"I'm sorry, but the full agent couldn't be initialized correctly. Here's what you asked: '{query_text}'",
                            "thinking": [
                                {"type": "mock_response", "description": "Generated mock response", "duration_ms": 100, "content": "Mock thinking process"}
                            ]
                        }
                        
                    def get_documents(self, query):
                        """Return empty document list"""
                        return []
                
                return MockAgent()

# Main app
def main():
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
    
    /* Thinking process styling - DeepSeek R1 inspired */
    .thinking-container {
        background-color: #f9f9f9;
        border-radius: 8px;
        border-left: 3px solid #2e7adc;
        padding: 15px;
        margin: 15px 0;
        font-family: monospace;
    }
    
    .thinking-header {
        color: #2e7adc;
        font-weight: bold;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 5px;
    }
    
    .thinking-step {
        position: relative;
        margin-bottom: 15px;
        padding-left: 20px;
        border-left: 1px solid #ddd;
    }
    
    .thinking-step:before {
        content: '';
        position: absolute;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #4CAF50;
        left: -5px;
        top: 5px;
    }
    
    .thinking-error:before {
        background: #f44336;
    }
    
    .thinking-time {
        color: #777;
        font-size: 0.8em;
        display: inline-block;
        min-width: 60px;
    }
    
    .thinking-description {
        font-weight: bold;
        color: #333;
        margin-right: 10px;
    }
    
    .thinking-content {
        margin-top: 5px;
        white-space: pre-wrap;
        background-color: #f0f0f0;
        padding: 5px;
        border-radius: 5px;
        font-size: 0.9em;
        border-left: 2px solid #ccc;
    }
    
    /* For the ChatGPT-style typing animation */
    .token-by-token {
        display: inline;
        white-space: pre-wrap;
        word-break: break-word;
        font-size: 16px;
        line-height: 1.5;
        overflow: visible !important;
        will-change: contents;
    }
    
    @keyframes cursor-blink {
        0% { opacity: 1; }
        50% { opacity: 0; }
        100% { opacity: 1; }
    }
    
    .cursor-effect {
        display: inline-block;
        width: 2px;
        height: 1em;
        background-color: #333;
        margin-left: 2px;
        vertical-align: middle;
        animation: cursor-blink 0.8s infinite;
        will-change: opacity;
    }
    
    /* Code block styling */
    pre {
        background-color: #f0f0f0;
        padding: 10px;
        border-radius: 5px;
        overflow-x: auto;
        margin: 10px 0;
        border-left: 3px solid #2e7adc;
    }
    
    code {
        font-family: monospace;
    }
    
    /* Improve the sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f5f7f9;
    }
    
    /* Custom button styling */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        border: none;
        color: white;
        background-color: #4CAF50;
        padding: 8px 16px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        transition-duration: 0.4s;
        cursor: pointer;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f0f2f6;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Additional JavaScript for the tokenized typing effect
    st.markdown("""
    <script type="text/javascript">
        function simulateTypingEffect(elementId, tokens, typingSpeed) {
            const container = document.getElementById(elementId);
            if (!container) return;
            
            let currentText = '';
            let tokenIndex = 0;
            
            const typeNextToken = () => {
                if (tokenIndex >= tokens.length) {
                    // Typing complete, remove cursor
                    const cursor = container.querySelector('.cursor-effect');
                    if (cursor) cursor.remove();
                    return;
                }
                
                const token = tokens[tokenIndex];
                currentText += token + ' ';
                
                // Update the display with the current text and cursor
                container.innerHTML = `${currentText}<span class="cursor-effect"></span>`;
                
                // Scroll to bottom if needed
                if (container.scrollHeight > container.clientHeight) {
                    container.scrollTop = container.scrollHeight;
                }
                
                // Calculate delay based on token length - shorter delay for faster typing
                // Use a base speed that's much faster than before
                const delay = Math.min(50, Math.max(10, token.length * (typingSpeed / 20)));
                
                tokenIndex++;
                setTimeout(typeNextToken, delay);
            };
            
            // Start typing
            typeNextToken();
        }

        // Process code blocks in tokens for proper display
        function processCodeBlocks(tokens) {
            let inCodeBlock = false;
            let language = '';
            let codeContent = '';
            let processedTokens = [];
            
            tokens.forEach(token => {
                if (token.includes('```') && !inCodeBlock) {
                    // Start of code block
                    inCodeBlock = true;
                    const parts = token.split('```');
                    if (parts.length > 1) {
                        language = parts[1].trim();
                        processedTokens.push(parts[0]);
                        
                        if (parts.length > 2 && parts[2]) {
                            codeContent = parts[2];
                        } else {
                            codeContent = '';
                        }
                    }
                } else if (token.includes('```') && inCodeBlock) {
                    // End of code block
                    inCodeBlock = false;
                    const parts = token.split('```');
                    codeContent += (parts[0] || '');
                    
                    // Add the complete code block as HTML
                    processedTokens.push(`<pre><code class="language-${language}">${codeContent}</code></pre>`);
                    
                    if (parts.length > 1 && parts[1]) {
                        processedTokens.push(parts[1]);
                    }
                } else if (inCodeBlock) {
                    // Inside code block
                    codeContent += token + ' ';
                } else {
                    // Regular text
                    processedTokens.push(token);
                }
            });
            
            return processedTokens;
        }
    </script>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    
    # Create a shared queue in session state for thinking steps updates
    if 'thinking_updates_queue' not in st.session_state:
        st.session_state.thinking_updates_queue = queue.Queue()
    
    # App header
    st.title("Kevin AI Assistant")
    st.markdown("Ask me anything about Canadian universities or other topics!")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Settings")
        
        # Web search toggle
        use_web_search = st.checkbox("Enable Web Search", True, 
            help="Kevin will search the web for the most up-to-date information")
        
        # Typing animation toggle
        typing_animation = st.checkbox("Enable Typing Animation", True,
            help="Show a realistic typing animation like ChatGPT")
        
        # Typing speed slider (lower = faster)
        typing_speed = st.slider("Typing Speed", min_value=1, max_value=50, value=10, 
            help="Lower values make typing appear faster")
        
        # Show thinking process toggle
        show_thinking = st.checkbox("Show Thinking Process", True,
            help="Display Kevin's step-by-step thinking process")
        
        # Temperature slider
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1,
            help="Lower values = more deterministic, higher values = more creative")
        
        # Reset conversation button
        if st.button("Reset Conversation"):
            st.session_state.messages = []
            st.rerun()
    
    # Initialize agent if not already done
    if st.session_state.agent is None:
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
        
        # Start processing the query
        with st.spinner('Kevin is thinking...'):
            try:
                # Ensure agent exists
                if 'agent' not in st.session_state or st.session_state.agent is None:
                    st.session_state.agent = initialize_agent()
                    
                # Create a thinking indicator with typing animation
                thinking_indicator = st.empty()
                thinking_indicator.markdown(
                    """<div class="typing-indicator">
                        <span></span><span></span><span></span>
                    </div>""", 
                    unsafe_allow_html=True
                )
                
                # Initialize thinking display container
                if show_thinking:
                    # Create a container for thinking steps display
                    thinking_container = st.container()
                    # Store reference to empty container in session state
                    st.session_state.thinking_display = thinking_container
                    # Initialize empty steps list
                    st.session_state.current_thinking_steps = []
                    # Store whether to show thinking steps
                    st.session_state.show_thinking = show_thinking
                    
                    # Start background thread to monitor thinking steps
                    global thinking_thread_active, stop_thinking_thread
                    if not thinking_thread_active:
                        stop_thinking_thread.clear()
                        # Pass the agent reference directly
                        agent_ref = st.session_state.agent
                        thinking_thread = threading.Thread(
                            target=poll_thinking_steps_safe, 
                            args=(agent_ref, stop_thinking_thread)
                        )
                        thinking_thread.daemon = True
                        thinking_thread.start()
                        thinking_thread_active = True
                    
                    # Create a placeholder for periodic refreshes
                    refresh_placeholder = st.empty()
                    
                    # Use this placeholder to periodically check for updates
                    def check_thinking_updates():
                        global latest_thinking_steps, last_update_time
                        
                        # Get current time
                        current_time = time.time()
                        
                        # Only check every 0.3 seconds to avoid too many refreshes
                        if current_time - last_update_time > 0.3:
                            with thinking_steps_lock:
                                steps = latest_thinking_steps.copy() if latest_thinking_steps else []
                            
                            if steps and (not st.session_state.current_thinking_steps or 
                                          len(steps) > len(st.session_state.current_thinking_steps)):
                                st.session_state.current_thinking_steps = steps
                                update_thinking_display()
                                last_update_time = current_time
                        
                        # This will rerun every 0.3 seconds while the app is running
                        refresh_placeholder.empty()
                        time.sleep(0.3)
                    
                    # This is a safe way to do periodic updates in Streamlit
                    # It doesn't use threading for UI updates, just periodic refresh
                    check_thinking_updates()
                
                # Get response from agent
                response = st.session_state.agent.query(prompt, use_web_search=use_web_search)
                
                # Handle different response formats
                if isinstance(response, dict):
                    answer = response.get("output", response.get("answer", str(response)))
                    thinking_steps = response.get("thinking", [])
                else:
                    answer = str(response)
                    thinking_steps = []
                
                # Stop background thread
                stop_thinking_thread.set()
                thinking_thread_active = False

                # Final thinking steps update
                if show_thinking:
                    with thinking_steps_lock:
                        if latest_thinking_steps:
                            st.session_state.current_thinking_steps = latest_thinking_steps.copy()
                            update_thinking_display()
                
                # Clear thinking indicator
                thinking_indicator.empty()
                
                # Generate a unique ID for this response
                response_id = f"response-{hash(prompt)}-{int(time.time())}"
                
                # Display the answer with token-by-token typing animation if enabled
                if typing_animation:
                    # First, render the container with an empty div
                    response_placeholder = st.empty()
                    response_placeholder.markdown(
                        f'<div id="{response_id}" class="token-by-token"></div>',
                        unsafe_allow_html=True
                    )
                    
                    # Simulate token-by-token typing more realistically
                    # Split the answer into "tokens" - not perfect NLP tokens, but close enough
                    tokens = []
                    
                    # Process code blocks specially
                    code_pattern = r'```[\s\S]*?```'
                    text_parts = re.split(code_pattern, answer)
                    code_parts = re.findall(code_pattern, answer)
                    
                    all_parts = []
                    for i in range(max(len(text_parts), len(code_parts))):
                        if i < len(text_parts) and text_parts[i].strip():
                            all_parts.append(("text", text_parts[i]))
                        if i < len(code_parts):
                            all_parts.append(("code", code_parts[i]))
                    
                    # Process each part - create larger chunks for faster typing
                    for part_type, part in all_parts:
                        if part_type == "text":
                            # Split text into sentences for more natural chunking
                            sentences = re.split(r'(?<=[.!?])\s+', part)
                            for sentence in sentences:
                                if not sentence.strip():
                                    continue
                                
                                # For short sentences, keep them as one token
                                if len(sentence.split()) <= 6:
                                    tokens.append(sentence)
                                else:
                                    # For longer sentences, split into chunks of 4-6 words
                                    # This creates a faster, more fluid typing experience
                                    words = sentence.split()
                                    chunk_size = 5  # Larger chunks = faster typing
                                    for i in range(0, len(words), chunk_size):
                                        token = " ".join(words[i:min(i+chunk_size, len(words))])
                                        if token:
                                            tokens.append(token)
                        else:
                            # For code blocks, we add them as a single token
                            tokens.append(part)
                    
                    # Escape tokens for JavaScript
                    escaped_tokens = []
                    for token in tokens:
                        # Escape special characters for JavaScript
                        escaped = (token.replace("\\", "\\\\")
                                  .replace('"', '\\"')
                                  .replace("\n", "\\n")
                                  .replace("<", "&lt;")
                                  .replace(">", "&gt;"))
                        escaped_tokens.append(escaped)
                    
                    # Use JavaScript for the animation (much smoother than Python)
                    st.markdown(
                        f"""
                        <script>
                            // Set up typing effect when the page is ready
                            (function() {{
                                // Create the tokens array
                                const tokens = {str(escaped_tokens).replace("'", '"')};
                                
                                // Start animation right away with a faster speed
                                setTimeout(function() {{
                                    simulateTypingEffect("{response_id}", tokens, {max(1, typing_speed / 5)});
                                }}, 10);
                            }})();
                        </script>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Also display the full answer immediately after animation setup
                    # This ensures the answer is visible even if JavaScript fails
                    response_placeholder.markdown(answer, unsafe_allow_html=True)
                else:
                    # Display the full answer immediately
                    response_placeholder.markdown(answer, unsafe_allow_html=True)
                
                # Store response
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # Show thinking process if enabled
                if show_thinking and thinking_steps:
                    # We've already displayed thinking steps in real-time,
                    # so we don't need to create a new expander here
                    pass
            
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                response_placeholder.error(error_msg)
                if logger_available:
                    logger.error(f"Error generating response: {e}")
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

def process_code_blocks(text):
    """Process code blocks for proper display with markdown"""
    # This is a simplified approach - for a complete solution, 
    # you'd need a more sophisticated markdown parser
    parts = text.split("```")
    result = []
    
    for i, part in enumerate(parts):
        if i % 2 == 0:  # Regular text
            result.append(part)
        else:  # Code block
            # Handle language specification
            lang_split = part.split("\n", 1)
            if len(lang_split) > 1:
                lang, code = lang_split
                result.append(f"<pre><code class='language-{lang.strip()}'>{code}</code></pre>")
            else:
                result.append(f"<pre><code>{part}</code></pre>")
    
    return "".join(result)

# Function to update thinking display in the UI
def update_thinking_display():
    """Updates the thinking steps display in the UI"""
    # Only show if we have thinking steps and the setting is enabled
    if 'show_thinking' in st.session_state and st.session_state.show_thinking and 'current_thinking_steps' in st.session_state and st.session_state.current_thinking_steps:
        steps = st.session_state.current_thinking_steps
        if not steps:
            return
            
        # Instead of rendering the HTML directly, use Streamlit components
        with st.container():
            st.markdown("### Thinking Steps")
            st.write(f"Total steps: {len(steps)} | Total time: {sum((step.get('duration_ms', 0) for step in steps)) / 1000:.2f}s")
            
            # Display each thinking step individually
            for i, step in enumerate(steps):
                step_type = step.get("type", "step")
                description = step.get("description", "Thinking...")
                content = step.get("content", "")
                duration = step.get("duration_ms", 0) / 1000  # Convert to seconds
                error = step.get("error", False)
                
                # Create the step display using Streamlit components
                with st.expander(f"{description} ({duration:.2f}s)", expanded=True):
                    if content:
                        st.text(content)
                    
                    # Display error information if this is an error step
                    if error:
                        st.error("Error encountered during this step")
                        
            # Add a separator
            st.divider()

if __name__ == "__main__":
    main() 