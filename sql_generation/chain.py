import sys
import os
import re

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from embeddings.langchain_vector_db import get_retriever
from sql_validation.validator import validate_sql
from config.settings import settings
from utils.logger import get_logger

logger = get_logger("SQLChain")

# Enterprise-grade few-shot prompt
SYSTEM_PROMPT = """You are a Principal SQL Data Analyst working on an enterprise e-commerce database.
Your objective is to translate the user's natural language question into a highly optimized, syntactically correct SQLite query.

You will be provided with the schema of ONLY the tables that are semantically relevant to the question.
If the provided schema is insufficient to answer the question, do your best using ONLY the provided tables.

CRITICAL RULES:
1. ONLY return the raw SQL query. Do not wrap it in ```sql or provide any explanations.
2. Ensure you use the exact table and column names provided in the schema.
3. Use proper JOINs using the specified Foreign Keys.
4. Do NOT use DROP, DELETE, UPDATE, or INSERT. Only SELECT statements are allowed.
5. To calculate "revenue" or "sales", you MUST use the `subtotal` (or `quantity * unit_price`) from the `order_items` table. Never calculate revenue just by summing `price` from `products`.

Relevant Schema Context:
{context}

User Question: {question}
"""

def format_docs(docs):
    """Formats retrieved FAISS documents into a string context."""
    return "\n\n".join(doc.page_content for doc in docs)

def extract_sql(text: str) -> str:
    """Cleans up markdown formatting if the LLM ignores instructions."""
    text = text.strip()
    match = re.search(r'```(?:sql|sqlite)?\s*(.*?)```', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Sometimes it outputs just `sqlite` at the beginning
    text = re.sub(r'^(sqlite|sql)\s+', '', text, flags=re.IGNORECASE)
    return text.strip()

def build_sql_chain():
    """
    Builds the LangChain orchestration for Retrieval-Augmented SQL Generation.
    """
    retriever = get_retriever()
    llm = ChatGoogleGenerativeAI(model=settings.LLM_MODEL, temperature=0.0)
    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
    
    # LCEL (LangChain Expression Language) Pipeline
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
        | extract_sql
    )
    
    return chain

def generate_and_validate_sql(question: str, max_retries: int = 3) -> str:
    """
    Orchestrates the chain and validates the output. Retries if the SQL is invalid.
    """
    logger.info(f"Generating SQL for: '{question}'")
    chain = build_sql_chain()
    
    for attempt in range(1, max_retries + 1):
        try:
            sql = chain.invoke(question)
            logger.info(f"Attempt {attempt} Generated SQL: {sql}")
            
            is_valid, error_msg = validate_sql(sql)
            if is_valid:
                logger.info("SQL Validation passed.")
                return sql
            else:
                logger.warning(f"SQL Validation failed: {error_msg}. Retrying...")
                
                # In a more advanced implementation, we would pass the error_msg back to the LLM 
                # as a "Self-Correction" prompt. For this phase, we just retry.
                
        except Exception as e:
            logger.error(f"Error executing chain: {e}")
            break
            
    logger.error("Failed to generate valid SQL after maximum retries.")
    return ""

if __name__ == "__main__":
    # Ensure env is loaded
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
    
    q = "What are the names of the top 3 customers who spent the most money overall?"
    sql = generate_and_validate_sql(q)
    print("\nFINAL SQL:\n", sql)
