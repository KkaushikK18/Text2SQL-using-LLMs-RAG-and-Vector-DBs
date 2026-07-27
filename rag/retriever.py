import os
import json
import faiss
import numpy as np
from google import genai
from dotenv import load_dotenv

# Load env variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

# Paths
EMBEDDINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'embeddings')
FAISS_INDEX_PATH = os.path.join(EMBEDDINGS_DIR, "schema_index.faiss")
MAPPING_PATH = os.path.join(EMBEDDINGS_DIR, "index_mapping.json")

class SchemaRetriever:
    def __init__(self):
        if not os.path.exists(FAISS_INDEX_PATH) or not os.path.exists(MAPPING_PATH):
            raise FileNotFoundError("FAISS index or mapping not found. Please run embeddings/vector_db.py first.")
            
        self.index = faiss.read_index(FAISS_INDEX_PATH)
        with open(MAPPING_PATH, "r") as f:
            self.table_names = json.load(f)
            
        self.client = genai.Client()
        
    def retrieve_tables(self, question: str, top_k: int = 4) -> list[str]:
        """
        Embeds the user question and returns the names of the top_k most relevant tables.
        """
        # Embed question
        response = self.client.models.embed_content(
            model='gemini-embedding-2',
            contents=question,
        )
        query_vector = np.array([response.embeddings[0].values], dtype=np.float32)
        
        # Search FAISS index
        # D is distances, I is indices
        D, I = self.index.search(query_vector, k=top_k)
        
        relevant_tables = []
        for idx in I[0]:
            if idx != -1 and idx < len(self.table_names):
                relevant_tables.append(self.table_names[idx])
                
        return relevant_tables

if __name__ == "__main__":
    retriever = SchemaRetriever()
    q = "Show revenue by customer"
    tables = retriever.retrieve_tables(q)
    print(f"Question: {q}")
    print(f"Retrieved Tables: {tables}")
