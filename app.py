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
        text_dict (dict): The text extracted for each page number
    """
    text_dict = {}
    text = ""
    for pdf_file in pdf_files:
        print("Extracting text from {}".format(pdf_file.name))
        pdf_reader = PdfReader(pdf_file)

        # Extract the text from the PDF pages and add it to a dictionary
        for index, page in enumerate(pdf_reader.pages):
            current_page_text = page.extract_text()
            text_dict[index]=current_page_text
            text += current_page_text
    
    return text, text_dict
