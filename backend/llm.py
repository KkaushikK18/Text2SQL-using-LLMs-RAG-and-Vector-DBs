import os
import sys
from google import genai
from dotenv import load_dotenv

# Add embeddings to path so we can import schema_metadata
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'embeddings'))
from schema_metadata import TABLE_METADATA

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

SYSTEM_INSTRUCTION = """
You are an expert SQL Data Analyst. Your job is to translate a user's natural language question into a valid SQLite query.

Rules:
1. ONLY return the raw SQL query. Do not include markdown formatting like ```sql or explanations.
2. Use valid SQLite syntax.
3. Use JOINs appropriately based on the foreign keys provided in the schema.
4. If you don't know the answer or the query is ambiguous, try your best to write a working SQL query based ONLY on the tables provided.
"""

def generate_sql(user_question: str, relevant_tables: list[str]) -> str:
    """
    Calls the Gemini API to convert a natural language question into a SQL query,
    using only the schema of the provided relevant_tables.
    """
    try:
        client = genai.Client()
        
        # Build dynamic schema context
        schema_context = "Here is the schema of the relevant tables for this query:\n\n"
        for table in relevant_tables:
            if table in TABLE_METADATA:
                schema_context += f"Table: {table}\n"
                schema_context += f"Columns: {TABLE_METADATA[table]['schema']}\n\n"
                
        prompt = f"{SYSTEM_INSTRUCTION}\n\n{schema_context}\nUser Question: {user_question}\n\nSQL Query:"
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        sql = response.text.strip()
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
            
        return sql.strip()
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return ""
