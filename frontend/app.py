import streamlit as st
import requests
import json
import uuid
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from frontend.components.charts import render_chart

# Configure page
st.set_page_config(
    page_title="Enterprise AI Text-to-SQL",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme CSS is native in Streamlit, but we can add some custom styling
st.markdown("""
<style>
    .reportview-container {
        background: #0E1117;
    }
    .main {
        background: #0E1117;
    }
    .stChatInputContainer {
        border-top: 1px solid #4B4B4B;
    }
    .sql-box {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #00C853;
        font-family: monospace;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
# Use environment variable for deployment, default to localhost for local testing
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Initialize Session State
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    
if "messages" not in st.session_state:
    st.session_state.messages = []

def fetch_history():
    try:
        response = requests.get(f"{API_URL}/history?limit=10")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Settings")
    st.caption(f"Session ID: {st.session_state.session_id[:8]}")
    
    st.divider()
    st.subheader("📜 Recent Queries")
    history = fetch_history()
    
    if history:
        for item in history:
            icon = "✅" if item['is_successful'] else "❌"
            st.caption(f"{icon} {item['user_question']}")
    else:
        st.info("No query history yet.")

# --- MAIN APP ---
st.title("🔍 Enterprise AI Text-to-SQL")
st.markdown("Ask natural language questions about your E-commerce database.")

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display data and charts if present in the message
        if "sql" in message:
            st.markdown(f"**Generated SQL** (Executed in {message['execution_time']}ms)")
            st.code(message["sql"], language="sql")
            
        if "data" in message and message["data"]:
            st.dataframe(message["data"], use_container_width=True)
            render_chart(message["data"], message["columns"])
            
        if "error" in message and message["error"]:
            st.error(message["error"])
            
        if "summary" in message and message["summary"]:
            st.success(f"**Agent Insight:** {message['summary']}")

# Chat input
if prompt := st.chat_input("E.g., Which supplier generated the highest revenue in Electronics during the last quarter?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Analyzing schema and generating SQL..."):
            try:
                response = requests.post(
                    f"{API_URL}/query",
                    json={"question": prompt, "session_id": st.session_state.session_id}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    sql = data.get("sql_query")
                    exec_time = data.get("execution_time_ms")
                    columns = data.get("columns", [])
                    result_data = data.get("data", [])
                    
                    is_successful = data.get("is_successful", False)
                    error_msg = data.get("error_message", None)
                    
                    # Display SQL
                    st.markdown(f"**Generated SQL** (Executed in {exec_time}ms)")
                    st.code(sql, language="sql")
                    
                    if is_successful:
                        # Display Data
                        if result_data:
                            st.dataframe(result_data, use_container_width=True)
                            # Render Chart
                            render_chart(result_data, columns)
                        else:
                            st.info("Query executed successfully but returned no results.")
                    else:
                        st.error(f"SQL Execution Failed: {error_msg}")
                        
                    # Save to state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Here is the result for your query.",
                        "sql": sql,
                        "execution_time": exec_time,
                        "columns": columns,
                        "data": result_data,
                        "error": error_msg if not is_successful else None,
                        "summary": data.get("natural_language_summary")
                    })
                    
                    # Display Agent Insight
                    summary = data.get("natural_language_summary")
                    if summary:
                        st.success(f"**Agent Insight:** {summary}")
                        
                else:
                    error_detail = response.json().get("detail", "Unknown error")
                    st.error(f"Failed to execute query: {error_detail}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "I encountered an error.",
                        "error": error_detail
                    })
                    
            except requests.exceptions.ConnectionError:
                err = "Cannot connect to the FastAPI backend. Is it running on port 8000?"
                st.error(err)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "I encountered a connection error.",
                    "error": err
                })
