#!/usr/bin/env python3
"""
Test module for Streamlit web interface.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Handle dependency imports safely
STREAMLIT_AVAILABLE = False
LANGCHAIN_AVAILABLE = False

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    # Create a minimal mock if streamlit is not available
    st = MagicMock()
    st.session_state = {}

try:
    import langchain
    LANGCHAIN_AVAILABLE = True
except ImportError:
    pass

# Only import if dependencies are available
if STREAMLIT_AVAILABLE and LANGCHAIN_AVAILABLE:
    try:
        # Import agent setup
        from src.core.agent_setup import initialize_agent, initialize_test_agent
    except ImportError:
        # Create stub functions if imports fail
        def initialize_agent():
            return MagicMock()
        
        def initialize_test_agent():
            mock = MagicMock()
            mock.invoke.return_value = {"output": "Test response"}
            return mock
else:
    # Create stub functions if dependencies are missing
    def initialize_agent():
        return MagicMock()
    
    def initialize_test_agent():
        mock = MagicMock()
        mock.invoke.return_value = {"output": "Test response"}
        return mock

def main():
    """Main function for the Streamlit app UI test."""
    st.set_page_config(
        page_title="University Application Assistant",
        page_icon="🎓",
        layout="wide"
    )

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.title("University Application Assistant 🎓")
        st.markdown("""
        Welcome to your personal university application consultation session. 
        I'm here to help you:
        * Build your academic profile
        * Explore your interests and goals
        * Document your achievements
        * Guide you through the application process
        """)

        # Initialize chat session
        if "messages" not in st.session_state:
            st.session_state.messages = []
            # Use test agent for testing
            st.session_state.agent = initialize_test_agent()

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            # Get agent response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = st.session_state.agent.invoke({"input": prompt})
                    st.write(response["output"])
            st.session_state.messages.append({"role": "assistant", "content": response["output"]})

    # Sidebar for profile summary
    with col2:
        st.sidebar.title("Your Profile Summary")
        if hasattr(st.session_state.agent, 'memory') and hasattr(st.session_state.agent.memory, 'chat_memory'):
            mem = st.session_state.agent.memory.load_memory_variables({})
            profile = mem.get('student_profile', {})
            
            if profile:
                for category, data in profile.items():
                    st.sidebar.subheader(f"📋 {category.title()}")
                    if isinstance(data, dict):
                        for key, value in data.items():
                            st.sidebar.markdown(f"**{key}:** {value}")
                    elif isinstance(data, list):
                        for item in data:
                            st.sidebar.markdown(f"• {item}")
                    else:
                        st.sidebar.markdown(str(data))
            else:
                st.sidebar.info("Start chatting to build your profile!")

        # Add a clear chat button
        if st.sidebar.button("Clear Chat"):
            st.session_state.messages = []
            st.session_state.agent = initialize_test_agent()
            st.rerun()

class TestWebUI(unittest.TestCase):
    """Test the Streamlit web UI functions and components."""
    
    @unittest.skipIf(not STREAMLIT_AVAILABLE, "Streamlit not available")
    @patch('streamlit.set_page_config')
    def test_page_config(self, mock_set_page_config):
        """Test that page configuration is set correctly."""
        try:
            from src.web.app import load_config
            
            # Verify the actual app's config function works
            config = load_config()
            self.assertIsInstance(config, dict)
            
            # Call the test UI's main function
            main()
            
            # Verify that set_page_config was called
            mock_set_page_config.assert_called_once()
        except ImportError:
            self.skipTest("Required module not available")
    
    @unittest.skipIf(not STREAMLIT_AVAILABLE, "Streamlit not available")
    @patch('streamlit.columns')
    @patch('streamlit.title')
    @patch('streamlit.markdown')
    @patch('streamlit.chat_input')
    def test_ui_elements(self, mock_chat_input, mock_markdown, mock_title, mock_columns):
        """Test that UI elements are created correctly."""
        # Mock the Streamlit functionality
        mock_columns.return_value = [MagicMock(), MagicMock()]
        mock_chat_input.return_value = None
        
        # Set up session state
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Run the main function
        main()
        
        # Verify UI elements were created
        mock_title.assert_called_with("University Application Assistant 🎓")
        mock_markdown.assert_called()
        mock_columns.assert_called_with([2, 1])
    
    @unittest.skipIf(not STREAMLIT_AVAILABLE, "Streamlit not available")
    def test_agent_initialization(self):
        """Test that the agent is initialized correctly."""
        # Set up patching
        with patch('tests.test_webui.initialize_test_agent') as mock_initialize_agent:
            # Mock the agent initialization
            mock_agent = MagicMock()
            mock_agent.invoke.return_value = {"output": "Test response"}
            mock_initialize_agent.return_value = mock_agent
            
            # Set up session state
            if "messages" in st.session_state:
                del st.session_state.messages
            
            # Run the main function with mocked components
            with patch('streamlit.set_page_config'), \
                 patch('streamlit.columns', return_value=[MagicMock(), MagicMock()]), \
                 patch('streamlit.title'), \
                 patch('streamlit.markdown'), \
                 patch('streamlit.chat_input', return_value=None):
                main()
            
            # Verify agent was initialized
            mock_initialize_agent.assert_called_once()
            
            # Check session state was set correctly
            self.assertIn("messages", st.session_state)
            self.assertIn("agent", st.session_state)

if __name__ == "__main__":
    # Only run tests if executed directly
    unittest.main() 