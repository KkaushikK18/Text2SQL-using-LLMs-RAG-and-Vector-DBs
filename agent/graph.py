import os
import sys
import re
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from embeddings.langchain_vector_db import get_retriever
from sql_validation.validator import validate_sql
from api.execution import execute_query
from config.settings import settings
from utils.logger import get_logger

logger = get_logger("AgentGraph")

class AgentState(TypedDict):
    question: str
    reformulated_question: str
    schema_context: str
    golden_queries: str
    business_rules: str
    sql_query: str
    is_valid: bool
    validation_error: str
    execution_results: List[Dict[str, Any]]
    execution_error: str
    columns: List[str]
    summary: str
    execution_time_ms: float
    iterations: int

# Initialize LLM
llm = ChatGoogleGenerativeAI(model=settings.LLM_MODEL, temperature=0.0)

def extract_sql(text: str) -> str:
    """Extracts raw SQL from LLM response"""
    text = text.strip()
    match = re.search(r'```(?:sql|sqlite)?\s*(.*?)```', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    text = re.sub(r'^(sqlite|sql)\s+', '', text, flags=re.IGNORECASE)
    return text.strip()

def retrieve_schema_node(state: AgentState) -> AgentState:
    """Agent 1: Planner/Retriever - Advanced RAG"""
    logger.info("Agent: Retrieving Schema Context & Golden Queries")
    original_q = state["question"]
    
    # 1. Query Reformulation (LLM expands query for better FAISS semantic matching)
    reformulate_prompt = ChatPromptTemplate.from_template(
        "Extract the core SQL search entities and tables from this question to help a semantic search engine find the right database tables. Output only keywords.\nQuestion: {question}"
    )
    reformulated = (reformulate_prompt | llm).invoke({"question": original_q}).content
    logger.info(f"Reformulated Question for Search: {reformulated}")
    
    # 2. Schema Retrieval (using reformulated query)
    retriever = get_retriever()
    schema_docs = retriever.invoke(reformulated)
    schema_context = "\n\n".join(doc.page_content for doc in schema_docs)
    
    # 3. Golden Queries Retrieval (using original query)
    from embeddings.golden_queries_db import get_golden_retriever
    try:
        golden_docs = get_golden_retriever().invoke(original_q)
        golden_context = "\n\n".join(doc.page_content for doc in golden_docs)
    except Exception as e:
        logger.warning(f"Golden queries retrieval failed: {e}")
        golden_context = "No golden examples found."
        
    # 4. Semantic Layer / Business Glossary
    from config.glossary import get_business_rules
    business_rules = get_business_rules(original_q)
    
    return {
        "reformulated_question": reformulated,
        "schema_context": schema_context,
        "golden_queries": golden_context,
        "business_rules": business_rules,
        "iterations": state.get("iterations", 0)
    }

def generate_sql_node(state: AgentState) -> AgentState:
    """Agent 2: SQL Coder - Writes or fixes SQL"""
    current_iter = state.get('iterations', 0)
    logger.info(f"Agent: Generating SQL (Attempt {current_iter + 1})")
    
    prompt = """You are a Principal SQL Coder for an SQLite e-commerce database.
    
    User Question: {question}
    
    Relevant Schema:
    {schema_context}
    
    Business Rules & Definitions:
    {business_rules}
    
    Similar Golden Queries (Examples to learn from):
    {golden_queries}
    
    Previous SQL Attempt: {sql_query}
    Validation Error: {validation_error}
    Execution Error: {execution_error}
    
    INSTRUCTIONS:
    1. If there are previous errors, analyze them and FIX the SQL query.
    2. Use ONLY the tables and columns provided in the schema.
    3. Adhere strictly to the Business Rules provided above.
    4. Use the Golden Queries as structural inspiration if they match the intent.
    5. SECURE SYSTEM PROTOCOL: You are strictly forbidden from modifying data (NO DROP, DELETE, UPDATE, INSERT). If the user asks to modify data, DO NOT attempt to fake the result by aliasing columns (e.g. `0 AS price`). Instead, you MUST return exactly this query: SELECT 'ERROR: Destructive operations (UPDATE/DELETE/DROP) are strictly forbidden in this environment.' AS security_violation;
    6. Output ONLY the raw SQL query without explanations or markdown formatting.
    """
    
    prompt_template = ChatPromptTemplate.from_template(prompt)
    chain = prompt_template | llm
    
    response = chain.invoke({
        "question": state["question"],
        "schema_context": state.get("schema_context", ""),
        "business_rules": state.get("business_rules", ""),
        "golden_queries": state.get("golden_queries", ""),
        "sql_query": state.get("sql_query", "None"),
        "validation_error": state.get("validation_error", "None"),
        "execution_error": state.get("execution_error", "None")
    })
    
    raw_sql = extract_sql(response.content)
    logger.info(f"Generated SQL: {raw_sql}")
    return {"sql_query": raw_sql, "iterations": current_iter + 1}

def execute_sql_node(state: AgentState) -> AgentState:
    """Agent 3: Reviewer/Executor - Validates and runs the SQL"""
    logger.info("Agent: Validating and Executing SQL")
    sql = state["sql_query"]
    
    # 1. Validate
    is_valid, val_err = validate_sql(sql)
    if not is_valid:
        logger.warning(f"Validation failed: {val_err}")
        return {"is_valid": False, "validation_error": val_err, "execution_error": ""}
        
    # 2. Execute
    result = execute_query(sql)
    if result["status"] == "error":
        logger.warning(f"Execution failed: {result['error']}")
        return {
            "is_valid": True, 
            "validation_error": "", 
            "execution_error": result["error"],
            "execution_results": [],
            "columns": [],
            "execution_time_ms": result.get("execution_time_ms", 0.0)
        }
        
    logger.info(f"Execution successful! Retrieved {len(result['data'])} rows.")
    return {
        "is_valid": True,
        "validation_error": "",
        "execution_error": "",
        "execution_results": result["data"],
        "columns": result["columns"],
        "execution_time_ms": result.get("execution_time_ms", 0.0)
    }

def analyze_results_node(state: AgentState) -> AgentState:
    """Agent 4: Data Scientist - Summarizes the final results"""
    logger.info("Agent: Analyzing Final Results")
    prompt = """You are an expert Data Analyst.
    
    User Question: {question}
    Data Results: {execution_results}
    Errors (if any): {execution_error}
    
    INSTRUCTIONS:
    If there are errors, briefly apologize and say the data couldn't be retrieved.
    If there are results, write a very concise (1-2 sentences) natural language business summary answering the user's question using the data provided.
    Do NOT mention the SQL query itself in your summary. Make it sound professional.
    """
    prompt_template = ChatPromptTemplate.from_template(prompt)
    chain = prompt_template | llm
    
    results_str = str(state.get("execution_results", []))[:2000]
    
    response = chain.invoke({
        "question": state["question"],
        "execution_results": results_str,
        "execution_error": state.get("execution_error", "")
    })
    
    return {"summary": response.content.strip()}

def should_continue(state: AgentState):
    """Router: Decides if we need to loop back to fix errors or move to analysis"""
    is_successful = state.get("is_valid", False) and not state.get("execution_error", "")
    
    if is_successful:
        logger.info("Router: Success! Moving to Analyst.")
        return "analyze"
        
    if state["iterations"] >= 3:
        logger.warning("Router: Max retries reached. Moving to Analyst to report failure.")
        return "analyze"
        
    logger.info("Router: Errors found. Looping back to SQL Coder to fix.")
    return "generate"

# Build the LangGraph Workflow
workflow = StateGraph(AgentState)

workflow.add_node("retrieve", retrieve_schema_node)
workflow.add_node("generate", generate_sql_node)
workflow.add_node("execute", execute_sql_node)
workflow.add_node("analyze", analyze_results_node)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", "execute")

# ReAct Loop (Conditional Edges)
workflow.add_conditional_edges(
    "execute",
    should_continue,
    {
        "generate": "generate",
        "analyze": "analyze"
    }
)

workflow.add_edge("analyze", END)

# Compile the agentic graph
agent_app = workflow.compile()

def run_agentic_pipeline(question: str) -> dict:
    """Entry point for the API"""
    logger.info(f"=== Starting Agentic Workflow for: '{question}' ===")
    initial_state = {
        "question": question,
        "iterations": 0
    }
    final_state = agent_app.invoke(initial_state)
    return final_state
