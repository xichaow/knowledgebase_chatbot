#!/usr/bin/env python3
"""
Custom retriever that works with Pinecone directly
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

from langchain.schema import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
from pydantic import Field

class CustomPineconeRetriever(BaseRetriever):
    """Custom Pinecone retriever that works with direct Pinecone client"""
    
    # Define allowed fields
    index_name: str = Field(default="")
    namespace: str = Field(default="")
    k: int = Field(default=4)
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, index_name: str, namespace: str, k: int = 4, **kwargs):
        super().__init__(
            index_name=index_name,
            namespace=namespace,
            k=k,
            **kwargs
        )
        
        # Initialize Pinecone client (store as private attributes)
        PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
        pc = Pinecone(api_key=PINECONE_API_KEY)
        self._index = pc.Index(index_name)
        
        # Initialize embeddings
        self._embeddings = OpenAIEmbeddings()
        
        print(f"✅ CustomPineconeRetriever initialized: {index_name}/{namespace}")
    
    def _get_relevant_documents(
        self, 
        query: str,
        *, 
        run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Get relevant documents for a query"""
        
        try:
            # Create query embedding
            query_embedding = self._embeddings.embed_query(query)
            
            # Query Pinecone directly
            result = self._index.query(
                vector=query_embedding,
                top_k=self.k,
                namespace=self.namespace,
                include_metadata=True
            )
            
            # Convert to LangChain documents
            documents = []
            for match in result.matches:
                if match.metadata and 'source' in match.metadata:
                    doc = Document(
                        page_content=match.metadata['source'],
                        metadata={
                            "score": match.score,
                            "id": match.id,
                            "namespace": self.namespace
                        }
                    )
                    documents.append(doc)
            
            print(f"🔍 CustomRetriever found {len(documents)} documents for: '{query}'")
            return documents
            
        except Exception as e:
            print(f"❌ Custom retriever error: {e}")
            return []
    
    def search_documents(self, query: str) -> List[Document]:
        """Public method for testing"""
        from langchain_core.callbacks import CallbackManagerForRetrieverRun
        run_manager = CallbackManagerForRetrieverRun.get_noop_manager()
        return self._get_relevant_documents(query, run_manager=run_manager)

def test_custom_retriever():
    """Test the custom retriever"""
    
    print("🧪 Testing Custom Pinecone Retriever")
    print("=" * 35)
    
    try:
        retriever = CustomPineconeRetriever(
            index_name="jr-lab",
            namespace="apra-information",
            k=4
        )
        
        test_queries = ["What is CPS 230?", "cps230", "operational risk"]
        
        for query in test_queries:
            print(f"\n❓ Query: '{query}'")
            docs = retriever.search_documents(query)
            
            if docs:
                for i, doc in enumerate(docs, 1):
                    preview = doc.page_content[:80].replace('\n', ' ')
                    score = doc.metadata.get('score', 'N/A')
                    print(f"  {i}. Score: {score:.4f} - {preview}...")
                print("✅ Custom retriever working!")
            else:
                print("❌ No documents found")
        
        return retriever
        
    except Exception as e:
        print(f"❌ Custom retriever test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_custom_retriever()