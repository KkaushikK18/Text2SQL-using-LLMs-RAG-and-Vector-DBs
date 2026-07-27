import sys
import os

# Add parent directory to path to import rag
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.llm import generate_sql
from backend.db import query_database
from rag.retriever import SchemaRetriever
import json

def main():
    print("Welcome to Text2SQL V2 Pipeline (with RAG)!")
    
    try:
        print("Initializing Vector DB Retriever...")
        retriever = SchemaRetriever()
        print("Retriever initialized successfully.\n")
    except Exception as e:
        print(f"Error initializing retriever: {e}")
        print("Make sure you have run 'python embeddings/vector_db.py' to generate the FAISS index first.")
        return

    print("Type your question below (or 'exit' to quit):")
    
    while True:
        question = input("\n> ")
        if question.lower() in ('exit', 'quit'):
            break
            
        if not question.strip():
            continue
            
        print("\n[1/4] Retrieving relevant tables (RAG)...")
        # Ask for slightly more tables if schema is complex, 4 is usually good for a query
        relevant_tables = retriever.retrieve_tables(question, top_k=4)
        print(f" -> Relevant tables found: {', '.join(relevant_tables)}")
            
        print("[2/4] Generating SQL...")
        sql_query = generate_sql(question, relevant_tables)
        
        if not sql_query:
            print("Failed to generate SQL.")
            continue
            
        print(f"Generated SQL:\n{sql_query}\n")
        
        print("[3/4] Executing Query...")
        result = query_database(sql_query)
        
        if result["error"]:
            print(f"Error executing SQL: {result['error']}")
            continue
            
        print("[4/4] Results:")
        print(f"Columns: {result['columns']}")
        print(f"Row count: {len(result['results'])}")
        
        if len(result['results']) > 0:
            print("First 5 rows:")
            print(json.dumps(result['results'][:5], indent=2))
        else:
            print("No rows returned.")

if __name__ == "__main__":
    main()
