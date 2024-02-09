import streamlit as st
from PyPDF2 import PdfReader
import os, re, io
import tempfile
#import nougat
from pdf2image import convert_from_path
import fitz
from sentence_transformers import SentenceTransformer
import numpy as np
import sqlite3
import openai

class RAG:
     
    def __init__(self, db_path, llm_api_key, embedding_model='all-MiniLM-L6-v2', chunk_size=250, overlap=25, search_threshold=0.8, max_token_length=512, cache_size=1000, verbose=False):
        self.db_path = db_path
        self.db = sqlite3.connect(db_path)
        self.llm_api_key = llm_api_key
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.search_threshold = search_threshold
        self.max_token_length = max_token_length
        self.cache_size = cache_size
        self.text_dict = {}
        self.verbose = verbose
        self.initialize_database()
        self.model = SentenceTransformer(embedding_model)
        self.llm_engine = 'gpt-3.5-turbo'

    def initialize_database(self):
        """
        Initializes the database by creating necessary tables.
        """
        cursor = self.db.cursor()

        # Create the text_chunks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS text_chunks (
            id INTEGER PRIMARY KEY,
            chunk TEXT NOT NULL,
            pdf_filename TEXT NOT NULL,
            page_number INTEGER NOT NULL
        )
    ''')

        # Create the embeddings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                chunk_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                FOREIGN KEY (chunk_id) REFERENCES text_chunks (id)
            )
        ''')

        self.db.commit()
    

    def clear_database(self):
        # clear the database if desired by the user
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM text_chunks")
        cursor.execute("DELETE FROM embeddings")
        self.db.commit()

    def extract_and_store_text(self, pdf_files):
        """
        Extracts text from PDF files, chunks it, and stores it in the database.
        
        Args:
            pdf_files: List of PDF files to process.
        """
        # Extract text from PDF files
        text_dict = self.get_text(pdf_files)

        # Chunk the extracted text
        chunks = self.chunk_text(text_dict)

        # Store the chunks in the database
        self.store_chunks(chunks)

        self.create_embeddings()

        return chunks

    def get_text(self, pdf_files):
        """
        Function to extract the text from one or more PDF file

        Args:
            pdf_files (files): The PDF files to extract the text from

        Returns:
            text (str): The text extracted from the PDF file
            text_dict (dict): The text extracted for each page number 
                with references to the source pdf and page
        """
        
        text_dict = {}
        for pdf_file in pdf_files:
            pdf = fitz.open(stream=pdf_file.read(), filetype="pdf")
            filename = pdf_file.name
            if self.verbose:
                print("Debug: processing file ", filename)

            for page_num in range(len(pdf)):
                if self.verbose:
                    print("Debug: now on page", page_num)
                page = pdf.load_page(page_num)

                current_page_text = page.get_text().replace('\n', ' ').replace('\u2009', ' ').replace('\xa0', ' ')
                current_page_text = ' '.join(current_page_text.split())


                # Store the temporary file name in the dictionary
                text_dict[(filename, page_num)] = (current_page_text)


        return text_dict


    def chunk_text(self, text_dict):
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
        overlap = self.overlap
        chunks = []
        current_chunk = ""
        current_references = []  # Stores (file_name, page_number) tuples
        for (file_name, page_number), (text) in text_dict.items():
        #for (file_name, page_number), text in text_dict.items():
            sentences = re.split(r'(?<=[.!?]) +', text)
            for sentence in sentences:
                if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
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

    def store_chunks(self, chunks):
        cursor = self.db.cursor()
        for chunk, references in chunks:
            
            pdf_filename, page_number = references[0]  
            if self.verbose:
                print("Debug: reference", pdf_filename, page_number)
            cursor.execute("INSERT INTO text_chunks (chunk, pdf_filename, page_number) VALUES (?, ?, ?)", 
                        (chunk, pdf_filename, page_number))

        self.db.commit()

    def create_embeddings(self):
        # Create embeddings for each chunk and store them
        cursor = self.db.cursor()
        cursor.execute("SELECT id, chunk FROM text_chunks")
        rows = cursor.fetchall()

        for row in rows:
            try:

                raw_text = row[1]
                cleaned_text = ''.join(char for char in raw_text if ord(char) < 128)
                embedding = self.model.encode(cleaned_text)
                cursor.execute("INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)", (row[0], embedding.tobytes()))

            # Rest of the code...
            except Exception as e:
                print(f"Error encoding text: {row[1]}")
                print("Error message:", e)
                continue  # Skip this row and continue with the next

        self.db.commit()

    def semantic_search(self, query):
        cleaned_query = ''.join(char for char in query if ord(char) < 128)
        query_embedding = self.model.encode(cleaned_query)
        cursor = self.db.cursor()
        cursor.execute("SELECT chunk_id, embedding FROM embeddings")
        rows = cursor.fetchall()

        max_similarity = -1
        best_chunk = None

        for row in rows:
            chunk_id = row[0]
            embedding = np.frombuffer(row[1], dtype=np.float32)
            similarity = np.dot(query_embedding, embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(embedding))

            if similarity > max_similarity:
                max_similarity = similarity
                best_chunk = chunk_id

        return best_chunk
    
    def get_chunk_by_id(self, chunk_id):
        """
        Retrieves a text chunk and its reference by the chunk ID.

        Args:
            chunk_id (int): The ID of the chunk to retrieve.

        Returns:
            tuple: A tuple containing the text chunk and its reference 
                   (PDF filename, page number).
        """
        cursor = self.db.cursor()
        cursor.execute("SELECT chunk, pdf_filename, page_number FROM text_chunks WHERE id = ?", (chunk_id,))
        result = cursor.fetchone()

        if result:
            chunk, pdf_filename, page_number = result
            return chunk, (pdf_filename, page_number)
        else:
            return None, None



    def integrate_llm(self, prompt):
        message=[{"role": "assistant", "content": "You are an expert in this content, helping to explain the text"}, {"role": "user", "content": prompt}]
        try:
            response = openai.chat.completions.create(
                model='gpt-4',  
                messages=message,
                max_tokens=250,  
                temperature=0.1  
            )
            # Extracting the content from the response
            chat_message = response.choices[0].message
            print(chat_message)
            return chat_message.content
    
        except Exception as e:
            print(f"Error in generating response: {e}")
            return None
        

    def generate_response(self, query):
        best_chunk_id = self.semantic_search(query)
        if best_chunk_id is not None:
            cursor = self.db.cursor()
            cursor.execute("SELECT chunk FROM text_chunks WHERE id = ?", (best_chunk_id,))
            best_chunk = cursor.fetchone()[0]
            response = self.integrate_llm(best_chunk + "\n" + query)
            return response
        else:
            return "Sorry, I couldn't find a relevant response."
    
    def get_page_image(self, pdf_file, page_num):
        """
        Extracts and returns a specific page image from a PDF file.

        Args:
            pdf_file: The PDF file to extract the image from.
            page_num: The page number to extract the image for.

        Returns:
            BytesIO object containing the image.
        """
        pdf = fitz.open(stream=pdf_file.read(), filetype="pdf")
        page = pdf.load_page(page_num)
        page_image = page.get_pixmap()

        image_bytes = io.BytesIO()
        page_image.save(image_bytes, 'png')
        image_bytes.seek(0)

        return image_bytes
