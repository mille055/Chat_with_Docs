import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import pymupdf, python-Levenshtein, nltk

def get_text(pdf_files):
    """
    Function to extract the text from one or more PDF file

    Args:
        pdf_files (files): The PDF files to extract the text from

    Returns:
        text (str): The text extracted from the PDF file
    """
  
    text = ""
    for pdf_file in pdf_files:
        print("Extracting text from {}".format(pdf_file.name))
        pdf_reader = PdfReader(pdf_file)

        # Extract the text from the PDF pages and add it to the raw text variable
        for page in pdf_reader.pages:
            text += page.extract_text()
    
    return text
