#!/usr/bin/env python3
"""
Streamlit web interface for Kevin that uses the FastAPI backend.
This version avoids direct dependencies on core modules and communicates exclusively
through the API service.
"""

import os
import sys
import streamlit as st
import requests
import json
import time
import threading
import queue
import sseclient
import uuid
from urllib.parse import urljoin
from typing import Dict, List, Any, Optional, Union, Tuple

# Set page configuration
st.set_page_config(
    page_title="Kevin AI Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("kevin-web-ui")

# Constants
DEFAULT_API_URL = "http://localhost:8000"
THINKING_POLL_INTERVAL = 0.2  # seconds
CONVERSATION_ID_KEY = "conversation_id"
MESSAGES_KEY = "messages"
API_URL_KEY = "api_url"
THINKING_STEPS_KEY = "thinking_steps"
THINKING_UPDATES_KEY = "thinking_updates_queue"
STREAMING_KEY = "streaming_active"

# Initialize session state
def init_session_state():
    """Initialize Streamlit session state variables."""
    if MESSAGES_KEY not in st.session_state:
        st.session_state[MESSAGES_KEY] = []
    
    if CONVERSATION_ID_KEY not in st.session_state:
        st.session_state[CONVERSATION_ID_KEY] = None
    
    if API_URL_KEY not in st.session_state:
        st.session_state[API_URL_KEY] = DEFAULT_API_URL
    
    if THINKING_STEPS_KEY not in st.session_state:
        st.session_state[THINKING_STEPS_KEY] = []
    
    if THINKING_UPDATES_KEY not in st.session_state:
        st.session_state[THINKING_UPDATES_KEY] = queue.Queue()
    
    if STREAMING_KEY not in st.session_state:
        st.session_state[STREAMING_KEY] = False

# API client for Kevin API
class KevinApiClient:
    """Client for interacting with the Kevin API."""
    
    def __init__(self, base_url: str = DEFAULT_API_URL):
        """Initialize the API client with the base URL."""
        self.base_url = base_url
        self.session = requests.Session()
    
    def _url(self, path: str) -> str:
        """Construct a full URL for the given path."""
        return urljoin(self.base_url, path)
    
    def check_health(self) -> bool:
        """Check if the API is healthy."""
        try:
            response = self.session.get(self._url("/api/health"))
            response.raise_for_status()
            data = response.json()
            return data.get("status") == "ok"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_root_info(self) -> Dict[str, Any]:
        """Get information about the API."""
        try:
            response = self.session.get(self._url("/"))
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get API info: {e}")
            return {"error": str(e)}
    
    def query_chat(self, 
                  query: str, 
                  use_web_search: bool = False,
                  conversation_id: Optional[str] = None,
                  stream: bool = False) -> Dict[str, Any]:
        """Submit a chat query to the API."""
        try:
            data = {
                "query": query,
                "use_web_search": use_web_search,
                "stream": stream
            }
            
            if conversation_id:
                data["conversation_id"] = conversation_id
            
            response = self.session.post(
                self._url("/api/chat/query"),
                json=data
            )
            
            # Handle redirect for streaming
            if response.status_code == 307:
                return {"redirect": True, "location": response.headers.get("Location")}
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Chat query failed: {e}")
            return {"error": str(e)}
    
    def stream_chat_query(self, 
                         query: str, 
                         use_web_search: bool = False,
                         conversation_id: Optional[str] = None,
                         on_thinking_start=None,
                         on_answer_chunk=None,
                         on_thinking_step=None,
                         on_done=None) -> None:
        """Stream a chat query with callback functions for different events."""
        params = {
            "query": query,
            "use_web_search": use_web_search
        }
        
        if conversation_id:
            params["conversation_id"] = conversation_id
        
        try:
            response = self.session.get(
                self._url("/api/chat/query/stream"),
                params=params,
                stream=True
            )
            response.raise_for_status()
            
            # Process the streaming response
            client = sseclient.SSEClient(response)
            result = {"chunks": [], "thinking_steps": [], "conversation_id": None}
            
            for event in client.events():
                if event.event == "thinking_start" and on_thinking_start:
                    data = json.loads(event.data)
                    on_thinking_start(data)
                
                elif event.event == "answer_chunk" and on_answer_chunk:
                    data = json.loads(event.data)
                    result["chunks"].append(data.get("chunk", ""))
                    on_answer_chunk(data)
                
                elif event.event == "thinking_step" and on_thinking_step:
                    data = json.loads(event.data)
                    result["thinking_steps"].append(data)
                    on_thinking_step(data)
                
                elif event.event == "done" and on_done:
                    data = json.loads(event.data)
                    result["conversation_id"] = data.get("conversation_id")
                    result["duration_seconds"] = data.get("duration_seconds")
                    on_done(data)
                    break
            
            return result
        except Exception as e:
            logger.error(f"Streaming chat query failed: {e}")
            if on_done:
                on_done({"error": str(e)})
            return {"error": str(e)}
    
    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Get a conversation by ID."""
        try:
            response = self.session.get(
                self._url(f"/api/chat/conversations/{conversation_id}")
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            return {"error": str(e)}
    
    def search_documents(self, 
                        query: str, 
                        limit: int = 5,
                        include_content: bool = True) -> Dict[str, Any]:
        """Search for documents in the vector store."""
        try:
            params = {
                "query": query,
                "limit": limit,
                "include_content": include_content
            }
            
            response = self.session.get(
                self._url("/api/search/documents"),
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return {"error": str(e)}
    
    def search_web(self, 
                  query: str, 
                  limit: int = 5) -> Dict[str, Any]:
        """Search the web for information."""
        try:
            params = {
                "query": query,
                "limit": limit
            }
            
            response = self.session.get(
                self._url("/api/search/web"),
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {"error": str(e)}
    
    def get_document_by_id(self, 
                          document_id: str,
                          include_content: bool = True) -> Dict[str, Any]:
        """Get a document by ID."""
        try:
            params = {
                "include_content": include_content
            }
            
            response = self.session.get(
                self._url(f"/api/documents/get/{document_id}"),
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return {"error": str(e)}
    
    def admin_action(self, 
                    action: str,
                    parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform an administrative action."""
        try:
            data = {
                "action": action
            }
            
            if parameters:
                data["parameters"] = parameters
            
            response = self.session.post(
                self._url("/api/admin"),
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Admin action failed: {e}")
            return {"error": str(e)}

# Custom Streamlit components
def thinking_steps_container():
    """Create a container for displaying thinking steps."""
    with st.expander("Thinking Steps", expanded=False):
        thinking_placeholder = st.empty()
        return thinking_placeholder

def update_thinking_steps(placeholder, thinking_steps):
    """Update the thinking steps display."""
    if not thinking_steps:
        placeholder.markdown("*No thinking steps available yet.*")
        return
    
    markdown = ""
    for i, step in enumerate(thinking_steps):
        description = step.get("description", "Unknown step")
        duration = step.get("duration", None)
        duration_str = f" ({duration:.2f}s)" if duration else ""
        
        markdown += f"### Step {i+1}: {description}{duration_str}\n\n"
        
        # Handle result or error
        if "result" in step and step["result"]:
            if isinstance(step["result"], str):
                markdown += f"**Result:**\n```\n{step['result']}\n```\n\n"
            elif isinstance(step["result"], dict):
                markdown += f"**Result:**\n```json\n{json.dumps(step['result'], indent=2)}\n```\n\n"
            else:
                markdown += f"**Result:** {str(step['result'])}\n\n"
        
        if "error" in step and step["error"]:
            markdown += f"**Error:**\n```\n{step['error']}\n```\n\n"
    
    placeholder.markdown(markdown)

def show_chat_message(message):
    """Display a chat message in the Streamlit UI."""
    role = message.get("role", "assistant")
    content = message.get("content", "")
    
    with st.chat_message(role):
        st.markdown(content)

def handle_api_error(error_msg):
    """Display an API error message."""
    st.error(f"API Error: {error_msg}")
    st.info("Make sure the Kevin API server is running. You can start it with: `kevin --mode api`")

def simulate_typing(placeholder, text, speed=10):
    """Simulate typing animation for text output."""
    full_text = ""
    for char in text:
        full_text += char
        placeholder.markdown(full_text + "▌")
        time.sleep(1.0 / speed)
    placeholder.markdown(full_text)

# Streaming response handler
def handle_streaming_response(query, use_web_search=False, conversation_id=None):
    """Handle streaming response from the API."""
    # Create the message containers
    st.session_state[STREAMING_KEY] = True
    st.session_state[THINKING_STEPS_KEY] = []
    
    # Add user message
    st.session_state[MESSAGES_KEY].append({"role": "user", "content": query})
    show_chat_message({"role": "user", "content": query})
    
    # Prepare response containers
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response_placeholder.markdown("*Thinking...*")
    
    # Create thinking steps container if enabled
    show_thinking = st.session_state.get("show_thinking", True)
    thinking_placeholder = thinking_steps_container() if show_thinking else None
    
    # Accumulated content
    accumulated_content = []
    
    # Event handlers
    def on_thinking_start(data):
        logger.info(f"Thinking started: {data}")
        if thinking_placeholder and show_thinking:
            thinking_placeholder.markdown("*Starting to think...*")
    
    def on_answer_chunk(data):
        chunk = data.get("chunk", "")
        accumulated_content.append(chunk)
        full_content = "".join(accumulated_content)
        response_placeholder.markdown(full_content + "▌" if st.session_state.get("typing_animation", True) else full_content)
    
    def on_thinking_step(data):
        logger.info(f"Thinking step: {data}")
        if thinking_placeholder and show_thinking:
            st.session_state[THINKING_STEPS_KEY].append(data)
            update_thinking_steps(thinking_placeholder, st.session_state[THINKING_STEPS_KEY])
    
    def on_done(data):
        logger.info(f"Streaming completed: {data}")
        full_content = "".join(accumulated_content)
        response_placeholder.markdown(full_content)
        
        # Save the conversation ID
        if "conversation_id" in data:
            st.session_state[CONVERSATION_ID_KEY] = data["conversation_id"]
        
        # Add the assistant's message to history
        if full_content:
            st.session_state[MESSAGES_KEY].append({
                "role": "assistant", 
                "content": full_content,
                "thinking_steps": st.session_state[THINKING_STEPS_KEY]
            })
        
        # Mark streaming as complete
        st.session_state[STREAMING_KEY] = False
    
    # Initialize API client
    api_client = KevinApiClient(st.session_state[API_URL_KEY])
    
    # Start streaming
    api_client.stream_chat_query(
        query=query,
        use_web_search=use_web_search,
        conversation_id=conversation_id,
        on_thinking_start=on_thinking_start,
        on_answer_chunk=on_answer_chunk,
        on_thinking_step=on_thinking_step,
        on_done=on_done
    )

# Non-streaming response handler
def handle_standard_response(query, use_web_search=False, conversation_id=None):
    """Handle non-streaming response from the API."""
    # Initialize API client
    api_client = KevinApiClient(st.session_state[API_URL_KEY])
    
    # Add user message
    st.session_state[MESSAGES_KEY].append({"role": "user", "content": query})
    show_chat_message({"role": "user", "content": query})
    
    # Show thinking indicator
    with st.chat_message("assistant"):
        with st.spinner("Kevin is thinking..."):
            # Send the query
            response = api_client.query_chat(
                query=query,
                use_web_search=use_web_search,
                conversation_id=conversation_id,
                stream=False
            )
    
    # Handle potential errors
    if "error" in response:
        handle_api_error(response["error"])
        return
    
    # Handle redirect (should not happen with stream=False)
    if response.get("redirect", False):
        st.warning(f"Unexpected redirect response. Please try again.")
        return
    
    # Extract response data
    answer = response.get("answer", "No answer provided.")
    thinking_steps = response.get("thinking_steps", [])
    
    # Save the conversation ID
    if "conversation_id" in response:
        st.session_state[CONVERSATION_ID_KEY] = response["conversation_id"]
    
    # Display the answer
    with st.chat_message("assistant"):
        if st.session_state.get("typing_animation", True):
            response_placeholder = st.empty()
            simulate_typing(response_placeholder, answer, st.session_state.get("typing_speed", 10))
        else:
            st.markdown(answer)
    
    # Save the assistant's message to history
    st.session_state[MESSAGES_KEY].append({
        "role": "assistant", 
        "content": answer,
        "thinking_steps": thinking_steps
    })
    
    # Display thinking steps if enabled
    if st.session_state.get("show_thinking", True) and thinking_steps:
        with thinking_steps_container() as container:
            update_thinking_steps(container, thinking_steps)

# Main function
def main():
    """Main function for the Streamlit app."""
    # Initialize session state
    init_session_state()
    
    # Page title and description
    st.title("Kevin AI Assistant")
    st.markdown("Ask me anything about Canadian universities or other topics!")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Settings")
        
        # API configuration
        st.subheader("API Connection")
        api_url = st.text_input("API URL", value=st.session_state[API_URL_KEY])
        
        if api_url != st.session_state[API_URL_KEY]:
            st.session_state[API_URL_KEY] = api_url
        
        # Test API connection
        if st.button("Test Connection"):
            with st.spinner("Testing API connection..."):
                api_client = KevinApiClient(api_url)
                is_healthy = api_client.check_health()
                
                if is_healthy:
                    st.success("API connection successful!")
                    info = api_client.get_root_info()
                    st.json(info)
                else:
                    st.error("Failed to connect to the API. Please check the URL and ensure the server is running.")
        
        # Query settings
        st.subheader("Query Settings")
        use_web_search = st.checkbox("Enable Web Search", True,
            help="When enabled, Kevin can search the web for recent information")
        
        streaming = st.checkbox("Enable Streaming", True,
            help="When enabled, the response will stream in real-time")
        
        # UI settings
        st.subheader("UI Settings")
        typing_animation = st.checkbox("Enable Typing Animation", True,
            help="When enabled, responses will appear as if they are being typed")
        
        typing_speed = st.slider("Typing Speed", min_value=1, max_value=50, value=10,
            help="Speed of typing animation (higher is faster)")
        
        show_thinking = st.checkbox("Show Thinking Process", True,
            help="When enabled, shows the AI's reasoning process")
        
        # Save settings to session state
        st.session_state["use_web_search"] = use_web_search
        st.session_state["streaming"] = streaming
        st.session_state["typing_animation"] = typing_animation
        st.session_state["typing_speed"] = typing_speed
        st.session_state["show_thinking"] = show_thinking
        
        # Reset conversation
        if st.button("Reset Conversation"):
            st.session_state[MESSAGES_KEY] = []
            st.session_state[CONVERSATION_ID_KEY] = None
            st.session_state[THINKING_STEPS_KEY] = []
            st.rerun()
    
    # Display chat history
    for message in st.session_state[MESSAGES_KEY]:
        show_chat_message(message)
    
    # Chat input
    if prompt := st.chat_input("Ask about Canadian universities..."):
        # Check if streaming is already in progress
        if st.session_state.get(STREAMING_KEY, False):
            st.warning("A response is already being generated. Please wait...")
            return
        
        # Process the query
        conversation_id = st.session_state.get(CONVERSATION_ID_KEY)
        use_web_search = st.session_state.get("use_web_search", True)
        streaming = st.session_state.get("streaming", True)
        
        if streaming:
            handle_streaming_response(prompt, use_web_search, conversation_id)
        else:
            handle_standard_response(prompt, use_web_search, conversation_id)

# Sample questions section
def render_sample_questions():
    """Render a section with sample questions."""
    st.markdown("### Sample Questions")
    
    cols = st.columns(2)
    
    sample_questions = [
        "What are the admission requirements for international students at UBC?",
        "How much does tuition cost for computer science at University of Toronto?",
        "What scholarships are available for students at McGill University?",
        "Compare the engineering programs at Waterloo and University of Toronto.",
        "What are the application deadlines for Fall 2023 at Queen's University?",
        "Tell me about student housing options at Western University."
    ]
    
    for i, col in enumerate(cols):
        for j in range(i, len(sample_questions), 2):
            question = sample_questions[j]
            if col.button(question, key=f"sample_{j}"):
                # Simulate entering the question in the chat input
                st.session_state["_last_query"] = question
                # Need to rerun to trigger the chat input
                st.rerun()

# CSS styling
def apply_custom_css():
    """Apply custom CSS styling to the app."""
    st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .thinking-step {
        border-left: 3px solid #4CAF50;
        padding-left: 10px;
        margin-bottom: 15px;
    }
    
    .thinking-step-header {
        font-weight: bold;
        color: #4CAF50;
    }
    
    .thinking-result {
        background: #f5f5f5;
        padding: 10px;
        border-radius: 5px;
        margin-top: 5px;
        font-family: monospace;
    }
    
    .thinking-error {
        background: #ffebee;
        color: #d32f2f;
        padding: 10px;
        border-radius: 5px;
        margin-top: 5px;
        font-family: monospace;
    }
    
    .streamlit-expanderHeader {
        font-size: 1.1em;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    apply_custom_css()
    main()
    render_sample_questions() 