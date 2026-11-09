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

class MetricsResponse(BaseModel):
    total_queries: int
    success_rate: float
    avg_execution_time_ms: float
    benchmark_accuracy: float
    ast_validity_rate: float
    self_correction_rate: float
    schema_recall_at_15: float
    token_cost_reduction: float
    security_violations_blocked: int
    complexity_breakdown: Dict[str, float]
    ablation_benchmarks: List[Dict[str, Any]]

class ColumnInfo(BaseModel):
    name: str
    type: str
    primary_key: bool
    nullable: bool
    unique: bool
    default: Optional[str] = None

class ForeignKeyInfo(BaseModel):
    column: str
    target_table: str
    target_column: str

class TableSchemaInfo(BaseModel):
    table_name: str
    category: str
    description: Optional[str] = None
    row_count: int
    columns: List[ColumnInfo]
    foreign_keys: List[ForeignKeyInfo]

class DatabaseSchemaResponse(BaseModel):
    total_tables: int
    total_columns: int
    total_rows: int
    categories: List[str]
    tables: List[TableSchemaInfo]

