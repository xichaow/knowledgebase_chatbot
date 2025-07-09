### --- Build the vector store for the given dataset --- ###
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from langchain.schema import Document
from langchain_pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyMuPDFLoader,
)
import os
import uuid
from pinecone import Pinecone, ServerlessSpec
import chainlit as cl

# Global variables
chunk_size = 1024
chunk_overlap = 100
PDF_STOREAGE_PATH = "./pdfs"

# Load the environment variables
load_dotenv()

# Pinecone client
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
index_name = "jr-lab"

# Initialize the Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
if index_name not in pc.list_indexes().names():
    pc.create_index(
        index_name=index_name,
        metric="cosine",
        dimension=1536,
        spec=ServerlessSpec(cloud="aws", region="us-west-2"),
    )

# Specify the embedding model
embeddings = OpenAIEmbeddings()


def process_pdfs(pdf_storage_path: str):
    pdf_directory = Path(pdf_storage_path)
    docs = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    pdf_files = list(pdf_directory.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF(s) in {pdf_storage_path}.")

    # Load PDFs and split into documents
    for pdf_path in pdf_files:
        print(f"Loading PDF: {pdf_path}")
        loader = PyMuPDFLoader(str(pdf_path))
        documents = loader.load()
        print(f"Loaded {len(documents)} document(s) from {pdf_path}.")
        for i, doc in enumerate(documents):
            print(f"Document {i}: {len(doc.page_content)} characters")
            print(f"Content preview: {doc.page_content[:100]}")
        split_docs = text_splitter.split_documents(documents)
        print(f"Split into {len(split_docs)} doc chunk(s) from {pdf_path}.")
        docs += split_docs

    print(f"Total doc chunks to process: {len(docs)}")
    doc_search = None  # Initialize to None
    # Convert text to embeddings
    for i, doc in enumerate(docs):
        print(f"Processing doc chunk {i+1}/{len(docs)}")
        embedding = embeddings.embed_query(doc.page_content)
        random_id = str(uuid.uuid4())
        doc_search = pc.Index(index_name)
        # Store the vector in Pinecone index
        doc_search.upsert(
            vectors=[
                {
                    "id": random_id,
                    "values": embedding,
                    "metadata": {"source": doc.page_content},
                }
            ],
            namespace="apra-information",
        )
        print("Vector stored in Pinecone index successfully.")
    return doc_search


def main():
    process_pdfs('./pdf/')


if __name__ == "__main__":
    main()
