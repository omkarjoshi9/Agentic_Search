import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.steamlit import displayInput, process_message_queue

import streamlit as st
from agent_graph.graph import create_graph, compile_workflow


server = 'groq'
model = 'llama3-8b-8192'
model_endpoint = None



print ("Creating graph and compiling workflow...")
graph = create_graph(server=server, model=model, model_endpoint=model_endpoint)
workflow = compile_workflow(graph)

# print(workflow.get_graph().draw_mermaid())

# workflow_image =workflow.get_graph().draw_mermaid()
# with open("workflow_image.png", "wb") as f:
#     f.write(workflow_image)



st.title("Agentic Search")

if __name__ == "__main__":
    verbose = False
    iterations = 40
    limit = {"recursion_limit": iterations}
    
    # Create a container for messages
    if 'message_container' not in st.session_state:
        st.session_state.message_container = st.container()
    
    # Display existing chat history
    placeholder = st.empty()  # Create an empty placeholder 
    i = 0
    user_data = displayInput()
    if user_data:
        
        if i >=1:
            for message in st.session_state.get('messages', []):
                st.chat_message(message["role"]).markdown(message["content"])
        i+=1
        with st.spinner('Processing...'):
            try:
                for event in workflow.stream(user_data, limit):
                    if verbose:
                        print("\nState Dictionary:", event)
                    process_message_queue()
                        

                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")