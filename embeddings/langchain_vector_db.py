import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from schema.extractor import get_schema_metadata
from config.settings import settings
from utils.logger import get_logger

logger = get_logger("VectorDB")

def build_langchain_vectorstore():
    """
    Extracts schema metadata, embeds it using LangChain, and stores it in FAISS.
    """
    logger.info("Building FAISS VectorStore using LangChain...")
    
    schema_metadata = get_schema_metadata()
    
    documents = []
    for meta in schema_metadata:
        doc = Document(
            page_content=meta["schema_text"],
            metadata={"table_name": meta["table_name"]}
        )
        documents.append(doc)
        
    logger.info(f"Generated {len(documents)} LangChain documents.")
    
    # Initialize embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model=settings.EMBEDDING_MODEL)
    
    # Build vectorstore
    vectorstore = FAISS.from_documents(documents, embeddings)
    
    # Save to disk
    vectorstore.save_local(settings.FAISS_INDEX_PATH)
    logger.info(f"FAISS vectorstore saved locally at {settings.FAISS_INDEX_PATH}")

def get_retriever():
    """
    Loads the FAISS index and returns a retriever.
    """
    embeddings = GoogleGenerativeAIEmbeddings(model=settings.EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(settings.FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    
    # We return the top 5 tables that match the semantic query
    return vectorstore.as_retriever(search_kwargs={"k": 5})

if __name__ == "__main__":
    build_langchain_vectorstore()
    
    # Test retriever
    logger.info("Testing retriever with query: 'Show me total revenue by customer'")
    retriever = get_retriever()
    docs = retriever.invoke("Show me total revenue by customer")
    for doc in docs:
        print(f"- {doc.metadata['table_name']}")
