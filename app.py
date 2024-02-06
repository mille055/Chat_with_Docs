import streamlit as st
from PyPDF2 import PdfReader
import os, re, io
import tempfile
#import nougat
from pdf2image import convert_from_path
import fitz

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
max_chunk_length = 250
chunk_overlap = 25

def get_text_and_images(pdf_files):
    """
    Function to extract the text from one or more PDF file

    Args:
        pdf_files (files): The PDF files to extract the text from

    Returns:
        text (str): The text extracted from the PDF file
        text_dict (dict): The text extracted for each page number
    """
    
    text_and_images_dict = {}
    for pdf_file in pdf_files:
        pdf = fitz.open(stream=pdf_file.read(), filetype="pdf")
        filename = pdf_file.name

        for page_num in range(len(pdf)):
            page = pdf.load_page(page_num)
            current_page_text = page.get_text().replace('\n', ' ').replace('\u2009', ' ').replace('\xa0', ' ')
            current_page_text = ' '.join(current_page_text.split())

            # Rasterize the page to PNG
            page_image = page.get_pixmap()
            # image_bytes = io.BytesIO()
            # page_image.save(image_bytes)
            # #page_image.writePNG(image_bytes)
            # image_bytes.seek(0)
            
            # Use a temporary file to save the image
            with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as temp_image_file:
                page_image.save(temp_image_file.name)
                temp_image_file.seek(0)

                # Store the temporary file name in the dictionary
                text_and_images_dict[(filename, page_num)] = (current_page_text, temp_image_file.name)



            text_and_images_dict[(filename, page_num)] = (current_page_text, image_bytes)

    return text_and_images_dict


def chunk_text_with_overlap(text_dict, max_length, overlap):
    """
    Splits text into chunks with a specified maximum length and overlap,
    trying to split at sentence endings when possible.

    Args:
        text_dict (dict): Dictionary with page numbers as keys and text as values.
        max_length (int): Maximum length of each chunk.
        overlap (int): Number of characters to overlap between chunks.

    Returns:
        list of tuples: Each tuple contains (chunk, (filename, page_numbers)), 
                        where `chunk` is the text chunk, 'filename' is the source file and `page_numbers` 
                        is a list of page numbers from which the chunk is derived.
    """

    chunks = []
    current_chunk = ""
    current_references = []  # Stores (file_name, page_number) tuples
    for (file_name, page_number), (text, _) in text_dict.items():
    #for (file_name, page_number), text in text_dict.items():
        sentences = re.split(r'(?<=[.!?]) +', text)
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > max_length and current_chunk:
                chunks.append((current_chunk, current_references.copy()))
                current_chunk = current_chunk[-overlap:]
                current_references = list(set(current_references + [(file_name, page_number)]))
            current_chunk += sentence + ' '
            current_references.append((file_name, page_number))
            current_references = sorted(set(current_references), key=current_references.index)

        if current_chunk:
            chunks.append((current_chunk, current_references))
            current_chunk = ""
            current_references = []

    return chunks

def convert_page_to_image(pdf_path, page_number):
    images = convert_from_path(pdf_path, first_page=page_number + 1, last_page=page_number + 1)
    return images[0] if images else None

    # chunks = []
    # current_chunk = ""
    # current_pages = []

    # for page_number, text in text_dict.items():
    #     sentences = re.split(r'(?<=[.!?]) +', text)
    #     for sentence in sentences:
    #         if len(current_chunk) + len(sentence) > max_length and current_chunk:
    #             # Save the current chunk and start a new one
    #             chunks.append((current_chunk, current_pages.copy()))
    #             # Start the new chunk with an overlap if possible
    #             current_chunk = current_chunk[-overlap:]
    #             current_pages = list(set(current_pages + [page_number]))
    #         current_chunk += sentence + ' '
    #         current_pages.append(page_number)
    #         # Ensuring the current page list is unique and ordered
    #         current_pages = sorted(set(current_pages), key=current_pages.index)

    #     # Add the last chunk if it's not empty
    #     if current_chunk:
    #         chunks.append((current_chunk, current_pages))
    #         current_chunk = ""
    #         current_pages = []

    # return chunks



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
        

        # Display the first chunk and its corresponding page image
        if text_chunks:
            chunk, references = text_chunks[0]
            st.write(chunk)
            for file_name, page_number in references:
                image = convert_page_to_image(file_name, page_number)
                if image:
                    st.image(image, caption=f"Page {page_number} of {file_name}")

    
    # Sidebar menu
    with st.sidebar:
        st.subheader("Document Uploader")

        # Document uploader
        pdf_files = st.file_uploader("Upload documents", type="pdf", key="upload", accept_multiple_files=True)

        # Process the document after the user clicks the button
        if st.button("Process Files"):
            with st.spinner("Processing"):
                text_and_images_dict = get_text_and_images(pdf_files)

                # Chunking the text
                text_chunks = chunk_text_with_overlap(text_and_images_dict, max_chunk_length, chunk_overlap)
            
                # Display the first chunk, its corresponding page image, and the source
                if text_chunks:
                    chunk, references = text_chunks[0]
                    st.write(chunk)
                    for file_name, page_number in references:
                        _, image_bytes = text_and_images_dict[(file_name, page_number)]
                        st.image(image_bytes, caption=f"Filename: {file_name}, Page: {page_number}")

                
                # Create a vector store for the chunks of text
                #vector_store = get_vectorstore(chunks)

                # Create a conversation chain for the chat model
                #st.session_state.conversations = get_conversation_chain(vector_store)

# Application entry point
if __name__ == "__main__":
    # Run the UI
    run_UI()