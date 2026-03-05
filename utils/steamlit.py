import streamlit as st
from utils.message_queue import global_message_queue

def displayResponse(response):
    """Thread-safe way to queue messages for display"""
    global_message_queue.put({
        "role": "assistant",
        "content": response
    })
    print("q.size",global_message_queue.qsize())

def displayInput(prompt_text: str = "Search Anything using Agentic search") -> dict:
    if user_input := st.chat_input(prompt_text):
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        message = {"role": "user", "content": user_input}
        st.session_state.messages.append(message)
        # st.session_state.message_container.mess(user_input)
        # st.chat_message(message["role"]).markdown(message["content"])
        for message in st.session_state.get('messages', []):
                st.chat_message(message["role"]).markdown(message["content"])
        return {"research_question": user_input, "loop": 0}
    return {}

def process_message_queue():
    """Process any pending messages in the queue"""
    while not global_message_queue.empty():
        message = global_message_queue.get()
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        st.session_state.messages.append(message)
        # st.session_state.message_container.markdown(message["content"])
        # st.chat_message(message["role"]).markdown(message["content"])
        st.chat_message(message["role"]).markdown(message["content"])

# Display existing messages

if "messages" in st.session_state:
    for message in st.session_state.messages:
        st.chat_message(message["role"]).markdown(message["content"])
