# Knowledge Base Chatbot

A RAG (Retrieval-Augmented Generation) chatbot that processes PDF documents and provides conversational Q&A using LangChain, Pinecone, and OpenAI.

## Features

- PDF document processing and text extraction
- Vector embeddings storage in Pinecone
- Conversational AI interface using Chainlit
- Memory-enabled chat conversations
- Source document references

## Setup

### Prerequisites

- Python 3.8+
- OpenAI API key
- Pinecone API key

### Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   PINECONE_API_KEY=your_pinecone_api_key_here
   ```

4. Add your PDF documents to the `pdf/` directory

### Usage

1. **Process PDFs and build vector store:**
   ```bash
   python vector_store.py
   ```

2. **Run the chatbot interface:**
   ```bash
   chainlit run app.py
   ```

3. Open your browser to `http://localhost:8000` to use the chatbot

## Project Structure

- `app.py` - Main Chainlit application
- `vector_store.py` - PDF processing and vector store creation
- `requirements.txt` - Python dependencies
- `pdf/` - Directory for PDF documents (not tracked in git)
- `.env` - Environment variables (not tracked in git)

## Security

This project uses `.gitignore` to prevent committing:
- API keys and environment variables
- PDF documents (may contain confidential data)
- Vector store data
- Cache and temporary files

Always review files before committing to ensure no sensitive data is included.