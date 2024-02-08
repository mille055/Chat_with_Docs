import streamlit as st
from PyPDF2 import PdfReader
import os, re, io
import tempfile
#import nougat
from pdf2image import convert_from_path
import fitz
from my_rag import RAG

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
chunk_size = 250
chunk_overlap = 25
DBPATH = 'data/db_file.db'
model = 'all-MiniLM-L6-v2'
st_rag = RAG(db_path = DBPATH, llm_api_key=OPENAI_API_KEY, embedding_model=model, chunk_size = chunk_size, overlap=chunk_overlap, verbose=True )


# main UI function
def run_UI():
    
    # Set the page tab title
    st.set_page_config(page_title="Chat with Docs", layout="wide")


    # Initialize the session state variables to store the conversations and chat history
    if "conversations" not in st.session_state:
        st.session_state.conversations = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    # Set the page title
    st.header("Chat with Docs: Interact with Your Documents")

    # Input text box for user query
    query = st.text_input("Ask a question")

    # Check if the user has entered a query/prompt
    if query:
        # Call the function to generate the response
        #generate_response(user_question)
        st.write('Your question is:', query )
        

        # # Display the first chunk and its corresponding page image
        # if text_chunks:
        #     chunk, references = text_chunks[0]
        #     st.write(chunk)
        #     # for file_name, page_number in references:
        #     #     #image = convert_page_to_image(file_name, page_number)
        #     #     image = text_and_images_dict[references][1]
        #     #     if image:
        #     #         st.image(image, caption=f"Page {page_number} of {file_name}")
        #     for file_name, page_number in references:
        #         _, image_bytes = text_and_images_dict[(file_name, page_number)]
        #         st.image(image_bytes, caption=f"Filename: {file_name}, Page: {page_number}")
    
    # Sidebar menu
    with st.sidebar:
        st.subheader("Document Uploader")

        # Document uploader
        pdf_files = st.file_uploader("Upload documents", type="pdf", key="upload", accept_multiple_files=True)

        # Process the document after the user clicks the button
        if st.button("Process Files"):
            with st.spinner("Processing"):
                text_dict = st_rag.get_text(pdf_files)

                # Chunking the text
                text_chunks = st_rag.chunk_text(text_dict)
                # Display the first chunk, its corresponding page image, and the source
                if text_chunks:
                    chunk, references = text_chunks[0]
                    st.write(chunk)
                    # for file_name, page_number in references:
                    #     # _, image_bytes = text_dict[(file_name, page_number)]
                        # st.image(image_bytes, caption=f"Filename: {file_name}, Page: {page_number}")

                
                # Create a vector store for the chunks of text
                #vector_store = get_vectorstore(chunks)

                # Create a conversation chain for the chat model
                #st.session_state.conversations = get_conversation_chain(vector_store)

# Application entry point
if __name__ == "__main__":
    # Run the UI
    run_UI()