"""
NovaBite AI Restaurant Assistant - Streamlit Frontend

A beautiful chat interface for interacting with the multi-agent RAG system.
"""

import streamlit as st
import requests
import uuid
from datetime import datetime

st.set_page_config(
    page_title="NovaBite AI Assistant",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B6B;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #E3F2FD;
        border-left: 4px solid #2196F3;
    }
    .assistant-message {
        background-color: #FFF3E0;
        border-left: 4px solid #FF9800;
    }
    .intent-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-top: 0.5rem;
    }
    .intent-knowledge {
        background-color: #4CAF50;
        color: white;
    }
    .intent-operations {
        background-color: #FF6B6B;
        color: white;
    }
    .intent-hybrid {
        background-color: #9C27B0;
        color: white;
    }
    .confidence-bar {
        height: 4px;
        background-color: #e0e0e0;
        border-radius: 2px;
        margin-top: 0.5rem;
    }
    .confidence-fill {
        height: 100%;
        background-color: #4CAF50;
        border-radius: 2px;
    }
    .tool-tag {
        display: inline-block;
        padding: 0.2rem 0.4rem;
        background-color: #f0f0f0;
        border-radius: 4px;
        font-size: 0.7rem;
        margin: 0.1rem;
    }
    .sidebar-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .status-online {
        color: #4CAF50;
        font-weight: bold;
    }
    .status-offline {
        color: #F44336;
        font-weight: bold;
    }
    .example-btn {
        margin: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = st.sidebar.text_input("API URL", value="http://localhost:8000")

# Session state initialization
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id" not in st.session_state:
    st.session_state.user_id = ""

# Sidebar
st.sidebar.markdown('<div class="sidebar-title">⚙️ Settings</div>', unsafe_allow_html=True)

# Session management
st.sidebar.subheader("Session")
st.sidebar.text_input("Session ID", value=st.session_state.session_id, disabled=True)
if st.sidebar.button("🔄 New Session"):
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.rerun()

# User ID
st.session_state.user_id = st.sidebar.text_input("User ID (optional)", 
                                                   placeholder="USR0001",
                                                   value=st.session_state.user_id)

def check_api_health():
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, {}
    except:
        return False, {}

is_healthy, health_data = check_api_health()

st.sidebar.subheader("Status")
if is_healthy:
    st.sidebar.markdown('<span class="status-online">● API Online</span>', unsafe_allow_html=True)
    st.sidebar.write(f"FAISS: {health_data.get('faiss_index', 'unknown')}")
    st.sidebar.write(f"Active Sessions: {health_data.get('active_sessions', 0)}")
else:
    st.sidebar.markdown('<span class="status-offline">● API Offline</span>', unsafe_allow_html=True)
    st.sidebar.warning("Make sure the API server is running!")
    st.sidebar.code("docker-compose up -d")

st.markdown('<div class="main-header">🍽️ NovaBite AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Your intelligent restaurant companion powered by multi-agent RAG</div>', 
              unsafe_allow_html=True)

st.subheader("💡 Try these examples:")
col1, col2, col3 = st.columns(3)

example_queries = [
    ("🌱 Vegan Options", "Do you have vegan pasta?"),
    ("📅 Book Table", "Book a table for 2 at nacrCity tomorrow at 7pm"),
    ("🎁 Check Points", "What are my loyalty points?"),
    ("⏰ Opening Hours", "What are your opening hours on weekends?"),
    ("🍕 Today's Special", "What's today's special at ShroukCity?"),
    ("🥜 Allergens", "Is the Caesar salad gluten-free?"),
]

for i, (label, query) in enumerate(example_queries):
    with [col1, col2, col3][i % 3]:
        if st.button(label, key=f"example_{i}", use_container_width=True):
            st.session_state.current_input = query
            st.rerun()

st.divider()

st.subheader("💬 Chat")

for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]
    
    if role == "user":
        st.markdown(f'''
        <div class="chat-message user-message">
            <strong>👤 You</strong><br>
            {content}
        </div>
        ''', unsafe_allow_html=True)
    else:
        intent = msg.get("intent", "")
        confidence = msg.get("confidence", 0)
        tools = msg.get("tools", [])
        
        intent_class = f"intent-{intent.lower()}" if intent else ""
        tools_html = " ".join([f'<span class="tool-tag">🔧 {t}</span>' for t in tools]) if tools else ""
        
        st.markdown(f'''
        <div class="chat-message assistant-message">
            <strong>🤖 NovaBite Assistant</strong><br>
            {content}<br>
            <span class="intent-badge {intent_class}">{intent}</span>
            {tools_html}
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: {confidence * 100}%"></div>
            </div>
            <small>Confidence: {confidence:.0%}</small>
        </div>
        ''', unsafe_allow_html=True)

def send_message():
    user_input = st.session_state.user_input
    if not user_input.strip():
        return
    
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    with st.spinner("🤖 Thinking..."):
        try:
            full_message = user_input
            if st.session_state.user_id:
                full_message = f"{user_input} (User: {st.session_state.user_id})"
            
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json={
                    "message": full_message,
                    "session_id": st.session_state.session_id
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data.get("response", "Sorry, I couldn't process that."),
                    "intent": data.get("intent", "UNKNOWN"),
                    "confidence": data.get("confidence", 0),
                    "tools": data.get("tools_used", []),
                    "timestamp": data.get("timestamp", datetime.now().isoformat())
                })
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Error: API returned status {response.status_code}",
                    "intent": "ERROR",
                    "confidence": 0,
                    "tools": []
                })
        except requests.exceptions.ConnectionError:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "❌ Cannot connect to API. Please ensure the server is running on " + API_BASE_URL,
                "intent": "ERROR",
                "confidence": 0,
                "tools": []
            })
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ Error: {str(e)}",
                "intent": "ERROR",
                "confidence": 0,
                "tools": []
            })
    
    # Clear input
    st.session_state.user_input = ""

# Input area
st.text_input(
    "Your message:",
    key="user_input",
    value=st.session_state.get("current_input", ""),
    on_change=send_message,
    placeholder="Ask about menu, book a table, check loyalty points..."
)

# Clear chat button
if st.button("🗑️ Clear Chat", type="secondary"):
    st.session_state.messages = []
    st.rerun()

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.8rem;">
    NovaBite AI Restaurant Assistant • Powered by LangChain, OpenAI, and FAISS<br>
    <a href="http://localhost:8000/docs" target="_blank">API Documentation</a> • 
    <a href="https://github.com/your-repo" target="_blank">GitHub</a>
</div>
""", unsafe_allow_html=True)
