import streamlit as st
from PyPDF2 import PdfReader
import os, re, io
import tempfile
from pdf2image import convert_from_path
import fitz
from my_rag import RAG

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
pdf_storage_dir = 'data/pdfs'
chunk_size = 500
chunk_overlap = 25
DBPATH = 'data/db_file.db'
model = 'all-MiniLM-L6-v2'
st_rag = RAG(db_path = DBPATH, llm_api_key=OPENAI_API_KEY, embedding_model=model, chunk_size = chunk_size, overlap=chunk_overlap, verbose=True )


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
        st.write('Your question is:', query )
        response = st_rag.generate_response(query)
        best_chunk_id = st_rag.semantic_search(query)
        best_chunk, best_reference = st_rag.get_chunk_by_id(best_chunk_id)
      
        if response:
            st.write('Response: ', response)
            #st.write('best_chunk', best_chunk)
            if best_reference:
                file_link = f"{best_reference[0]} (Page {best_reference[1] + 1})"
                if st.button(f"Show source page for {file_link}"):
                    image_bytes = get_page_image(best_reference[0], best_reference[1])
                    st.image(image_bytes, caption=f"Source: {file_link}")
                    st.write('Best chunk:', best_chunk)
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