import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'ecommerce.db')

def query_database(sql_query: str) -> dict:
    """
    Executes a read-only SQL query against the ecommerce database.
    Returns a dictionary with 'columns', 'results', and 'error' keys.
    """
    if "insert" in sql_query.lower() or "update" in sql_query.lower() or "delete" in sql_query.lower() or "drop" in sql_query.lower():
        return {"error": "Only read-only SELECT queries are allowed."}

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # To return dict-like rows
        cursor = conn.cursor()
        
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        
        columns = [description[0] for description in cursor.description] if cursor.description else []
        results = [dict(row) for row in rows]
        
        conn.close()
        return {
            "columns": columns,
            "results": results,
            "error": None
        }
    except Exception as e:
        return {
            "columns": [],
            "results": [],
            "error": str(e)
        }

if __name__ == "__main__":
    # Test query
    result = query_database("SELECT * FROM Categories;")
    print(json.dumps(result, indent=2))
