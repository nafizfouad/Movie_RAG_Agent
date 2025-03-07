"""
Main Streamlit application for the Movie RAG Agent.
"""
import os
import time
import streamlit as st
from dotenv import load_dotenv

from rag import MovieRAGAgent

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Movie RAG Agent",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
<style>
    .reportview-container {
        margin-top: -2em;
    }
    .stDeployButton {
        display:none;
    }
    .stTextInput > div > div > input {
        border-radius: 20px;
    }
    .stButton > button {
        border-radius: 20px;
        padding: 0.5em 1em;
    }
    .st-emotion-cache-1gulkj5 {
        background-color: #f0f0f0;
        padding: 1em;
        border-radius: 10px;
        margin-bottom: 1em;
    }
    .tool-call {
        background-color: #eef5ff;
        padding: 1em;
        border-radius: 8px;
        margin: 0.8em 0;
        border-left: 5px solid #4682B4;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .ai-message {
        background-color: #f0fff0;
        padding: 1em;
        border-radius: 10px;
        margin-top: 1em;
        margin-bottom: 1.5em;
        border-left: 5px solid #388e3c;
    }
    
    .human-message {
        background-color: #f0f8ff;
        padding: 1em;
        border-radius: 10px;
        margin-bottom: 1em;
        border-left: 5px solid #1976d2;
    }
    
    /* Style for tool call headers */
    .stMarkdown h3:contains("Tool Calls") {
        margin-top: 1em;
        margin-bottom: 0.5em;
        color: #4682B4;
        font-size: 1.2em;
    }
    
    /* Make expandable sections more attractive */
    .streamlit-expanderHeader {
        background-color: #f8f9fa !important;
        border-radius: 4px !important;
    }
    
    /* Style for expander content */
    .streamlit-expanderContent {
        background-color: #ffffff !important;
        border-top: none !important;
        padding: 1em !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "rag_agent" not in st.session_state:
    # Check for API key
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        openai_api_key = st.secrets.get("OPENAI_API_KEY", None)
    
    # Initialize the agent if key exists
    if openai_api_key:
        st.session_state.rag_agent = MovieRAGAgent(openai_api_key=openai_api_key)
        st.session_state.api_key_provided = True
    else:
        st.session_state.api_key_provided = False

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
    
if "tool_calls" not in st.session_state:
    st.session_state.tool_calls = []
    
if "needs_rerun" not in st.session_state:
    st.session_state.needs_rerun = False
    
if "processing" not in st.session_state:
    st.session_state.processing = False
    
if "current_query" not in st.session_state:
    st.session_state.current_query = None

# Add JavaScript for auto-scrolling to the latest message
if st.session_state.conversation_history:
    js = """
    <script>
        function scrollToBottom() {
            const messages = document.querySelectorAll('.stMarkdown');
            if (messages.length > 0) {
                const lastMessage = messages[messages.length - 1];
                lastMessage.scrollIntoView();
            }
        }
        // Delayed execution to ensure DOM is fully loaded
        setTimeout(scrollToBottom, 500);
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)

# Create callback functions for example queries
def use_example_interstellar():
    query = "Tell me about Interstellar"
    if query not in [msg.get("content", "") for msg in st.session_state.conversation_history if msg.get("role") == "human"]:
        process_with_input(query)

def use_example_matrix():
    query = "Find trailers for The Matrix"
    if query not in [msg.get("content", "") for msg in st.session_state.conversation_history if msg.get("role") == "human"]:
        process_with_input(query)

def process_with_input(custom_input=None):
    """Process either the user input from the text field or a custom input."""
    query = custom_input if custom_input else st.session_state.user_input
    if not query:
        return
    
    # Store current query for scrolling purposes
    st.session_state.current_query = query
    
    # Set processing flag
    st.session_state.processing = True
    
    # Clear the input field if it was the source
    if not custom_input:
        st.session_state.user_input = ""
    
    # Add user message to history immediately
    st.session_state.conversation_history.append({"role": "human", "content": query})
    
    # Set a flag to rerun to show the user's message
    st.session_state.needs_rerun = True

# Main application layout
st.title("🎬 Movie & TV Show RAG Agent")

# Sidebar with info and settings
with st.sidebar:
    st.header("About")
    st.markdown("""
    This is a Retrieval Augmented Generation (RAG) agent that can:
    - Search for movie and TV show information
    - Find IMDb ratings, release dates, and more
    - Search for trailers on YouTube
    - Answer general questions
    
    Just type your query in the chat box below!
    """)
    
    st.header("Settings")
    
    # API key input if not already provided
    if not st.session_state.api_key_provided:
        openai_api_key = st.text_input("OpenAI API Key", type="password")
        if st.button("Save API Key"):
            if openai_api_key:
                st.session_state.rag_agent = MovieRAGAgent(openai_api_key=openai_api_key)
                st.session_state.api_key_provided = True
                st.success("API key saved successfully!")
            else:
                st.error("Please enter a valid API key.")
    
    # Show session info and clear button
    if st.session_state.api_key_provided:
        st.success("✅ API Key configured")
        
        if st.button("Clear Conversation"):
            st.session_state.conversation_history = []
            st.session_state.tool_calls = []
            st.session_state.rag_agent = MovieRAGAgent(openai_api_key=st.session_state.rag_agent.openai_api_key)
            st.success("Conversation cleared!")

# Main chat area
chat_container = st.container()

# Process any ongoing query
if st.session_state.processing and st.session_state.current_query:
    with st.spinner(f"Processing query: {st.session_state.current_query}"):
        response, tool_calls = st.session_state.rag_agent.process_query(st.session_state.current_query)
        
        # Add assistant response to history
        st.session_state.conversation_history.append({
            "role": "ai", 
            "content": response,
            "tool_calls": tool_calls
        })
        
        # Reset processing state
        st.session_state.processing = False
        st.session_state.current_query = None
        
        # Trigger rerun to show response
        st.session_state.needs_rerun = True

# Display conversation history
with chat_container:
    # Create a placeholder for each message to help with scrolling
    message_placeholders = []
    
    for i, message in enumerate(st.session_state.conversation_history):
        message_container = st.container()
        message_placeholders.append(message_container)
        
        with message_container:
            if message["role"] == "human":
                st.markdown(f'<div class="human-message">💬 **You**: {message["content"]}</div>', unsafe_allow_html=True)
            else:  # AI message
                # Show tool calls
                if message.get("tool_calls"):
                    st.markdown("### 🔧 Tool Calls")
                    for i, tool_call in enumerate(message["tool_calls"]):
                        st.markdown(f'<div class="tool-call">', unsafe_allow_html=True)
                        st.markdown(f"**Tool #{i+1}**: {tool_call['tool']}")
                        st.markdown(f"**Input**: `{tool_call['input']}`")
                        
                        # Output in expander
                        with st.expander("Show Output", expanded=False):
                            st.json(tool_call['output'])
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                
                # Show the agent response
                st.markdown(f'<div class="ai-message">🎬 **Movie Agent**: {message["content"]}</div>', unsafe_allow_html=True)

# Input area
with st.container():
    st.text_input(
        "Ask me about a movie or TV show:",
        key="user_input",
        on_change=process_with_input,
        placeholder="e.g., 'Tell me about Inception' or 'Find trailers for Stranger Things'"
    )
    
    # Show example queries
    st.markdown("### Examples:")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎬 Tell me about Interstellar"):
            use_example_interstellar()
    
    with col2:
        if st.button("🍿 Find trailers for The Matrix"):
            use_example_matrix()

# Footer
st.markdown("---")
st.markdown("RAG Movie Agent | Built with LangChain, OpenAI, and Streamlit")

# Check if it needs to rerun
if st.session_state.needs_rerun:
    st.session_state.needs_rerun = False
    st.rerun()

# Run the app
if __name__ == "__main__":
    pass