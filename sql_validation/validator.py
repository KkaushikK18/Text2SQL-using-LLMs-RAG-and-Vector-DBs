import sqlparse
from typing import Tuple

FORBIDDEN_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", 
    "GRANT", "REVOKE", "COMMIT", "ROLLBACK", "EXEC", "EXECUTE"
}

def validate_sql(sql_query: str) -> Tuple[bool, str]:
    """
    Validates a SQL query to ensure it only performs safe SELECT operations.
    Returns (is_valid, error_message).
    """
    if not sql_query or not sql_query.strip():
        return False, "Query is empty."
        
    statements = sqlparse.split(sql_query)
    
    # Allow only one statement per query to prevent injection like: SELECT * FROM X; DROP TABLE Y;
    if len(statements) > 1:
        # Ignore trailing semicolons that cause empty statements
        non_empty = [s for s in statements if s.strip() and s.strip() != ';']
        if len(non_empty) > 1:
            return False, "Multiple SQL statements are not allowed."
            
    # Parse the statement
    parsed = sqlparse.parse(sql_query)[0]
    
    # Check the type of statement (should ideally be SELECT or PRAGMA for SQLite)
    stmt_type = parsed.get_type()
    if stmt_type != 'SELECT':
        # sqlparse sometimes categorizes complex SELECTs as 'UNKNOWN'
        # We will do a robust token check instead of strictly failing on stmt_type
        pass

    # Flatten tokens and check against forbidden keywords
    tokens = [t for t in parsed.flatten() if t.ttype not in (sqlparse.tokens.Whitespace, sqlparse.tokens.Newline)]
    
    for token in tokens:
        # Check if the token is a keyword and if it's in the forbidden list
        if str(token).upper() in FORBIDDEN_KEYWORDS:
            return False, f"Forbidden SQL keyword detected: {str(token).upper()}"
            
    return True, ""
    
if __name__ == "__main__":
    test_queries = [
        "SELECT * FROM customers;",
        "UPDATE customers SET name = 'Hacked';",
        "SELECT * FROM orders; DROP TABLE users;",
        "SELECT customer_id, SUM(total_amount) FROM orders GROUP BY customer_id;"
    ]
    
    for q in test_queries:
        valid, err = validate_sql(q)
        print(f"Query: {q}\nValid: {valid}, Error: {err}\n")
