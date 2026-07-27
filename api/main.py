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
from sql_generation.chain import generate_and_validate_sql
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
    
    # 1. Generate and Validate SQL
    sql = generate_and_validate_sql(request.question)
    
    if not sql:
        error_msg = "Failed to generate valid SQL query. Ensure your request complies with security rules."
        log_query_history(request.question, "", {"status": "error", "error": error_msg}, request.session_id)
        raise HTTPException(status_code=400, detail=error_msg)
        
    # 2. Execute SQL safely
    result = execute_query(sql)
    
    # 3. Log History
    log_query_history(request.question, sql, result, request.session_id)
    
    return QueryResponse(
        sql_query=sql,
        execution_time_ms=result.get("execution_time_ms", 0.0),
        is_successful=(result.get("status") == "success"),
        columns=result.get("columns", []),
        data=result.get("data", []),
        error_message=result.get("error")
    )

@app.get("/history", response_model=list[HistoryResponse])
def get_history(db: Session = Depends(get_db), limit: int = 50):
    history = db.query(QueryHistory).order_by(QueryHistory.created_at.desc()).limit(limit).all()
    return history

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
