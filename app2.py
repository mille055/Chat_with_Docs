import streamlit as st
from PyPDF2 import PdfReader
import os, re, io
import tempfile
from pdf2image import convert_from_path
import fitz
from collections import OrderedDict
from my_rag import RAG

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
pdf_storage_dir = 'data/pdfs'
chunk_size = 500 # 500 characters default
chunk_overlap = 25
top_k = 3 # number of chunks found in semantic search
DBPATH = 'data/db_file.db'
model = 'all-MiniLM-L6-v2'
st_rag = RAG(db_path = DBPATH, llm_api_key=OPENAI_API_KEY, embedding_model=model, chunk_size = chunk_size, overlap=chunk_overlap, top_k = top_k, verbose=True )


#gets the image of the source page
def get_page_image(pdf_filename, page_number):
    pdf_path = os.path.join(pdf_storage_dir, pdf_filename)
    
    try:
        pdf = fitz.open(pdf_path)
        page = pdf.load_page(page_number)

        # Convert the page to an image
        page_image = page.get_pixmap()

        # Get image data in PNG format and write to BytesIO
        image_bytes = io.BytesIO(page_image.tobytes("png"))
        
        return image_bytes
    except Exception as e:
        st.error(f"Error loading page image: {e}")
        return None



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
        #st.write('Your question is:', query )
        # get the RAG response and the references for display
        response = st_rag.generate_response(query)
        chunk_ids = st_rag.semantic_search(query)
        best_chunks_and_references = st_rag.get_chunks_by_ids(chunk_ids)
        
        # get the GPT response from just the initial prompt and query, no chunked context
        llm_response = st_rag.integrate_llm(query)
        print(llm_response)

        # create two columns
        col1, col2 = st.columns(2)

        with col1:
            with st.container():
                st.write('RAG Model Response:')
                st.markdown('---')  # Optional: Adds a horizontal line for better separation
                if response:
                    st.write(response)
                else:
                    st.write('No matching text from RAG model.')

        with col2:
            with st.container():
                st.write('GPT API Response:')
                st.markdown('---')  # Optional: Adds a horizontal line for better separation
                if llm_response:
                    st.write(llm_response)
                else:
                    st.write('No matching text from GPT API.')



        # if response:
        #     st.write('Response: ', response)
            #st.write('best_chunk', best_chunk)
        if best_chunks_and_references:
            index = 1 # to prevent duplicate links
            for chunk, reference in best_chunks_and_references:
                # reference tuple is filename, page number
                file_link = f"{reference[0]} (Page {reference[1] + 1}) ({index})"
                if st.button(f"Show source page for {file_link}"):
                    image_bytes = get_page_image(reference[0], reference[1])
                    st.image(image_bytes, caption=f"Source: {file_link}")
                    st.write('Chunk: ', chunk)
                index +=1 
        else:   
            st.write('No matching text.')

    
    # Sidebar menu
    with st.sidebar:
        st.subheader("Settings")

        # Sliders for chunk size and overlap
        if "chunk_size" not in st.session_state:
            st.session_state.chunk_size = 500
        if "chunk_overlap" not in st.session_state:
            st.session_state.chunk_overlap = 25

        st.session_state.chunk_size = st.slider("Chunk Size", min_value=100, max_value=1000, value=st.session_state.chunk_size)
        st.session_state.chunk_overlap = st.slider("Chunk Overlap", min_value=0, max_value=100, value=st.session_state.chunk_overlap)

        # Button to clear the database
        if st.button("Clear Database"):
            st_rag.clear_database()
            st.write("Database cleared.")

    with st.sidebar:
        st.subheader("Document Uploader")

        # Document uploader
        pdf_files = st.file_uploader("Upload documents", type="pdf", key="upload", accept_multiple_files=True)

        # Process the document after the user clicks the button
        if st.button("Process Files"):
            with st.spinner("Processing"):
                text_chunks = st_rag.extract_and_store_text(pdf_files)
              
                for pdf_file in pdf_files:
                    # Define the path to save the PDF
                    file_path = os.path.join(pdf_storage_dir, pdf_file.name)

                    # Write the contents of the uploaded file to a new file
                    with open(file_path, "wb") as f:
                        f.write(pdf_file.getbuffer())

                    st.write(f"Saved {pdf_file.name} to {pdf_storage_dir}")
 
            

# Application entry point
if __name__ == "__main__":
    # Run the UI
    run_UI()