from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    sql_query: str
    execution_time_ms: float
    is_successful: bool
    columns: List[str]
    data: List[Dict[str, Any]]
    error_message: Optional[str] = None
    natural_language_summary: Optional[str] = None

class HistoryResponse(BaseModel):
    id: int
    session_id: Optional[str]
    user_question: str
    generated_sql: Optional[str]
    execution_time_ms: Optional[float]
    is_successful: bool
    error_message: Optional[str]
    
    class Config:
        from_attributes = True
