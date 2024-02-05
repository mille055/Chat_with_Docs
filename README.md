# Chat_with_Docs
Code for a RAG from scratch that can be deployed online


This project is an implementation of a `Retrieval Augmented Generation`(RAG) System. It leverages the power of Python and the API from OpenAI to create an interactive chat experience with any PDF or document you have. 

## How It Works

1. **Upload Your Documents**: Users can upload one or more PDF(s) directly into the Streamlit app. The app also supports other file formats such as DOCX, and TXT.
2. **Text Preparation**: Once uploaded, the app extracts the text from the document(s) and splits into chunks.
3. **Embedding and Indexing**: The chunked text is then embedded using OpenAI embeddings and saved to a SQL database. 
4. **Streawmlit Interface**: Users can then navigate to the chat section of the app, where they can ask questions and engage in dialogue with the RAG-empowered chatbot. The embedded documents serve as the context needed to generate accurate and contextually relevant responses.

&nbsp;
## Running the Application 
Following are the steps to run the StreamLit Application: 

**1. Create a new conda environment and activate it:** 
```
conda create --name chat python=3.8.17
conda activate chat
```
**2. Install python package requirements:** 
```
pip install -r requirements.txt 
```
**4. Add OpenAI API Key**
```
Rename the env.example file to .env and add your OpenAI API key
```
**5. Run the application**
```
streamlit run app.py
```
