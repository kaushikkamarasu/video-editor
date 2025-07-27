import streamlit as st
import os
import asyncio
import sys
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Video Editor (MCP Edition)",
    page_icon="🎬",
    layout="wide",
)

# --- Title and Description ---
st.title("🎬 AI-Powered Video Editor (MCP Architecture)")
st.markdown("""
Welcome to the future of video editing! This version uses the **Multi-Component Protocol (MCP)** to automatically start and communicate with the editing tools.

**To get started:**
1.  Ensure `video_server.py` is in the same folder as this app.
2.  Enter your Groq API key in the sidebar below.
3.  Upload your video and start editing!
""")

# --- API Key Management ---
with st.sidebar:
    st.header("Configuration")
    st.markdown("Please enter your Groq API key to begin.")
    groq_api_key = st.text_input("Groq API Key", type="password")
    if groq_api_key:
        os.environ["GROQ_API_KEY"] = groq_api_key
        st.success("API Key set successfully!")
    else:
        st.warning("Groq API Key is required to use the editor.")

# --- File Upload and Session State ---
st.header("1. Upload Your Video")
uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "mov", "avi", "mkv"])

if "video_path" not in st.session_state:
    st.session_state.video_path = None
if "edited_video_path" not in st.session_state:
    st.session_state.edited_video_path = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "agent_executor" not in st.session_state:
    st.session_state.agent_executor = None


if uploaded_file is not None:
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    if not os.path.exists("outputs"):
        os.makedirs("outputs")

    file_path = os.path.join("uploads", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.session_state.video_path = file_path
    st.session_state.edited_video_path = file_path

# --- Video Display ---
if st.session_state.video_path:
    st.header("2. Preview Your Video")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original Video")
        st.video(st.session_state.video_path)
    with col2:
        st.subheader("Edited Video")
        if st.session_state.edited_video_path and os.path.exists(st.session_state.edited_video_path):
            st.video(st.session_state.edited_video_path)
        else:
            st.info("No edits have been made yet.")

# --- LangChain Agent Setup ---
async def setup_agent_async(llm):
    """Asynchronously sets up the LangChain agent by launching the server as a subprocess."""
    try:
        server_path = os.path.abspath("video_server.py")
        
        if not os.path.exists(server_path):
            st.error(f"Could not find the server script at {server_path}. Make sure 'video_server.py' is in the same directory as 'app.py'.")
            return None

        client = MultiServerMCPClient(
            {
                "video_editor": {
                    "command": sys.executable,
                    "args": [server_path],
                    "transport": "stdio",
                }
            }
        )
        tools = await client.get_tools()
        agent_executor = create_react_agent(llm, tools)
        return agent_executor
    except Exception as e:
        st.error(f"Failed to start or connect to the video server process. Error: {e}")
        return None

if groq_api_key and st.session_state.agent_executor is None:
    llm = ChatGroq(temperature=0, model_name="llama3-70b-8192")
    try:
        st.session_state.agent_executor = asyncio.run(setup_agent_async(llm))
        if st.session_state.agent_executor:
            st.success("Video editing server started and agent is ready!")
    except Exception as e:
        st.error(f"Error during agent setup: {e}")


# --- Chat Interface ---
st.header("3. Edit Your Video with Natural Language")

if st.session_state.video_path and groq_api_key:
    if st.session_state.agent_executor is None:
        st.warning("Agent is not initialized. Please ensure the API key is correct and 'video_server.py' exists.")
    else:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("e.g., 'trim the video from 5 to 10 seconds'"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking and editing..."):
                    agent_executor = st.session_state.agent_executor
                    messages = [
                        {"role": "user", "content": f"The current video is at {st.session_state.edited_video_path}. The user wants to: {prompt}"}
                    ]
                    response_stream = agent_executor.stream({"messages": messages})

                    final_response = ""
                    for chunk in response_stream:
                        if "messages" in chunk:
                            final_response = chunk["messages"][-1].content

                    st.markdown(final_response)

                    if "outputs/" in final_response:
                        try:
                            parts = final_response.split("outputs/")
                            if len(parts) > 1:
                                new_video_filename = parts[-1].strip().split()[0]
                                new_video_path = os.path.join("outputs", new_video_filename)
                                if os.path.exists(new_video_path):
                                    st.session_state.edited_video_path = new_video_path
                                else:
                                    st.error(f"Editor said it created a file, but it was not found: {new_video_path}")
                        except Exception as e:
                            st.error(f"Could not parse the output path from the response: {e}")


                    st.session_state.chat_history.append({"role": "assistant", "content": final_response})
                    st.rerun()

elif not groq_api_key:
    st.info("Please enter your Groq API key in the sidebar to enable the editor.")
else:
    st.info("Please upload a video to start editing.")

