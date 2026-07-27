import sys
import os
import time
import pandas as pd
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.connection import engine, SessionLocal
from database.models import QueryHistory
from utils.logger import get_logger

logger = get_logger("SQLExecution")

def execute_query(sql: str) -> dict:
    """
    Executes a validated SQL query against the database.
    Returns a dictionary with status, columns, and data (or error).
    """
    start_time = time.time()
    result_dict = {
        "status": "success",
        "columns": [],
        "data": [],
        "error": None,
        "execution_time_ms": 0
    }
    
    try:
        # Use pandas to easily load SQL results into a dict format
        df = pd.read_sql_query(sql, engine)
        result_dict["columns"] = df.columns.tolist()
        result_dict["data"] = df.to_dict(orient="records")
        
        logger.info(f"Query executed successfully, fetched {len(df)} rows.")
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        result_dict["status"] = "error"
        result_dict["error"] = str(e)
        
    execution_time = (time.time() - start_time) * 1000
    result_dict["execution_time_ms"] = round(execution_time, 2)
    
    return result_dict

def log_query_history(question: str, sql: str, result: dict, session_id: str = None):
    """
    Logs the query and its performance to the QueryHistory table.
    """
    db = SessionLocal()
    try:
        history = QueryHistory(
            session_id=session_id,
            user_question=question,
            generated_sql=sql,
            execution_time_ms=result.get("execution_time_ms"),
            is_successful=(result.get("status") == "success"),
            error_message=result.get("error")
        )
        db.add(history)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log query history: {e}")
    finally:
        db.close()
