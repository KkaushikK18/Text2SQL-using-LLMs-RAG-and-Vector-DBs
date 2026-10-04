import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import QueryHistory
from agent.graph import run_agentic_pipeline
from api.execution import execute_query, log_query_history
from api.schemas import QueryRequest, QueryResponse, HistoryResponse
from utils.logger import get_logger

logger = get_logger("API")

app = FastAPI(title="Enterprise Text-to-SQL API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/query", response_model=QueryResponse)
def execute_nl_query(request: QueryRequest):
    logger.info(f"Received query request: {request.question}")
    
    # Run the full agentic LangGraph workflow (ReAct Loop)
    final_state = run_agentic_pipeline(request.question)
    
    sql = final_state.get("sql_query", "")
    exec_time = final_state.get("execution_time_ms", 0.0)
    is_successful = final_state.get("is_valid", False) and not final_state.get("execution_error")
    columns = final_state.get("columns", [])
    result_data = final_state.get("execution_results", [])
    
    error_msg = None
    if not is_successful:
        error_msg = final_state.get("execution_error") or final_state.get("validation_error")
        
    summary = final_state.get("summary", "")
    
    # Log History
    log_query_history(request.question, sql, {"status": "success" if is_successful else "error", "error": error_msg, "execution_time_ms": exec_time}, request.session_id)
    
    if not is_successful and not sql:
        raise HTTPException(status_code=400, detail="Failed to generate valid SQL query.")
        
    return QueryResponse(
        sql_query=sql,
        execution_time_ms=exec_time,
        is_successful=is_successful,
        columns=columns,
        data=result_data,
        error_message=error_msg,
        natural_language_summary=summary
    )

@app.get("/history", response_model=list[HistoryResponse])
def get_history(db: Session = Depends(get_db), limit: int = 50):
    history = db.query(QueryHistory).order_by(QueryHistory.created_at.desc()).limit(limit).all()
    return history

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
