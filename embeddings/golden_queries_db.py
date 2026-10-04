import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config.settings import settings

# Enterprise "Golden Records" - Verified, perfect SQL queries for complex business questions.
GOLDEN_QUERIES = [
    {
        "q": "Which supplier generated the highest revenue?", 
        "sql": "SELECT s.name FROM suppliers s JOIN products p ON s.id = p.supplier_id JOIN order_items oi ON p.id = oi.product_id GROUP BY s.name ORDER BY SUM(oi.subtotal) DESC LIMIT 1;"
    },
    {
        "q": "What is the total revenue?", 
        "sql": "SELECT SUM(subtotal) FROM order_items;"
    },
    {
        "q": "Who are our VIP customers?", 
        "sql": "SELECT c.first_name, c.last_name, SUM(o.total_amount) as total_spent FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id HAVING total_spent > 1000;"
    },
    {
        "q": "Show me the top 5 most expensive products.", 
        "sql": "SELECT name, price FROM products ORDER BY price DESC LIMIT 5;"
    },
    {
        "q": "How many active orders do we have?", 
        "sql": "SELECT COUNT(*) FROM orders WHERE status IN ('processing', 'shipped');"
    }
]

def build_golden_vectorstore():
    """Builds a FAISS index of historically correct Golden Queries"""
    docs = []
    for item in GOLDEN_QUERIES:
        content = f"Question: {item['q']}\nSQL: {item['sql']}"
        docs.append(Document(page_content=content, metadata={"type": "golden_query"}))
    
    print("Building Golden Queries FAISS index...")
    embeddings = GoogleGenerativeAIEmbeddings(model=settings.EMBEDDING_MODEL)
    vectorstore = FAISS.from_documents(docs, embeddings)
    
    os.makedirs("embeddings/golden_index", exist_ok=True)
    vectorstore.save_local("embeddings/golden_index")
    print("Golden queries FAISS index built successfully at embeddings/golden_index")

def get_golden_retriever():
    """Returns the retriever for few-shot prompt injection"""
    embeddings = GoogleGenerativeAIEmbeddings(model=settings.EMBEDDING_MODEL)
    vectorstore = FAISS.load_local("embeddings/golden_index", embeddings, allow_dangerous_deserialization=True)
    return vectorstore.as_retriever(search_kwargs={"k": 2})

if __name__ == "__main__":
    build_golden_vectorstore()
