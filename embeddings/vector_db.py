import os
import json
import faiss
import numpy as np
from google import genai
from dotenv import load_dotenv

# Load env variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from schema_metadata import TABLE_METADATA

def build_vector_db():
    print("Initializing GenAI Client...")
    client = genai.Client()
    
    table_names = list(TABLE_METADATA.keys())
    embeddings_list = []
    
    print(f"Generating embeddings for {len(table_names)} tables...")
    for table_name in table_names:
        meta = TABLE_METADATA[table_name]
        # Create a rich text representation of the table for embedding
        text_to_embed = f"Table: {table_name}\nPurpose: {meta['description']}\nSchema: {meta['schema']}"
        
        response = client.models.embed_content(
            model='gemini-embedding-2',
            contents=text_to_embed,
        )
        embedding = response.embeddings[0].values
        embeddings_list.append(embedding)
        print(f" -> Embedded {table_name}")

    # Convert to numpy array
    embeddings_np = np.array(embeddings_list, dtype=np.float32)
    
    dimension = embeddings_np.shape[1]
    print(f"Embedding dimension: {dimension}")
    
    # Create FAISS index
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_np)
    
    # Save index
    faiss_path = os.path.join(os.path.dirname(__file__), "schema_index.faiss")
    faiss.write_index(index, faiss_path)
    
    # Save mapping (index to table name)
    mapping_path = os.path.join(os.path.dirname(__file__), "index_mapping.json")
    with open(mapping_path, "w") as f:
        json.dump(table_names, f)
        
    print(f"Successfully saved FAISS index to {faiss_path}")
    print(f"Successfully saved mapping to {mapping_path}")

if __name__ == "__main__":
    build_vector_db()
