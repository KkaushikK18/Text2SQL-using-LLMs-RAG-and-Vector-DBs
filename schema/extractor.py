import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.models import Base
from database.connection import engine
from sqlalchemy import text
from utils.logger import get_logger

logger = get_logger("SchemaExtractor")

TABLE_CATEGORIES = {
    "orders": ("Commerce & Sales", "Customer purchase orders and status tracking"),
    "order_items": ("Commerce & Sales", "Individual line items with quantities, prices and subtotals"),
    "payments": ("Commerce & Sales", "Payment transactions, methods, and processing states"),
    "coupons": ("Commerce & Sales", "Promotional discount codes, usage limits, and expiration"),
    "returns": ("Commerce & Sales", "Customer item return requests and refund approvals"),
    
    "categories": ("Catalog & Inventory", "Product taxonomy hierarchy and classifications"),
    "suppliers": ("Catalog & Inventory", "Vendors, contact emails, and performance ratings"),
    "products": ("Catalog & Inventory", "Product catalog with pricing, SKU, and vendor relationships"),
    "inventory": ("Catalog & Inventory", "Warehouse stock balances and reorder thresholds"),
    "reviews": ("Catalog & Inventory", "Customer product star ratings and qualitative reviews"),
    
    "customers": ("Customers & CRM", "Registered buyer profiles, contact info, and lifetime loyalty"),
    "addresses": ("Customers & CRM", "Customer billing and physical delivery addresses"),
    "wishlists": ("Customers & CRM", "Saved items for future customer consideration"),
    "support_tickets": ("Customers & CRM", "Customer service inquiries, priority, and resolution status"),
    "notifications": ("Customers & CRM", "System alerts and email notifications sent to users"),
    
    "shipping": ("Operations & System", "Courier fulfillment, tracking numbers, and delivery dates"),
    "admins": ("Operations & System", "Internal staff administrative users and permission roles"),
    "sessions": ("Operations & System", "Active user authentication web sessions"),
    "audit_logs": ("Operations & System", "Security audit trail recording critical system actions"),
    "query_history": ("Operations & System", "Execution log of all natural language questions and SQL queries"),
}

def get_detailed_schema() -> dict:
    """
    Extracts structured metadata for all tables including columns, types, constraints,
    foreign keys, row counts, and business categories for UI presentation.
    """
    tables_list = []
    total_columns = 0
    total_rows = 0

    # Read live row counts if DB is present
    row_counts = {}
    try:
        with engine.connect() as conn:
            for t_name in Base.metadata.tables.keys():
                try:
                    cnt = conn.execute(text(f"SELECT COUNT(*) FROM {t_name}")).scalar()
                    row_counts[t_name] = int(cnt or 0)
                except Exception:
                    row_counts[t_name] = 0
    except Exception as e:
        logger.warning(f"Could not connect to database for live row counts: {e}")

    for table_name, table in Base.metadata.tables.items():
        columns = []
        foreign_keys = []
        
        for col in table.columns:
            total_columns += 1
            col_type = str(col.type)
            default_val = str(col.default.arg) if col.default is not None and hasattr(col.default, 'arg') else None
            
            columns.append({
                "name": col.name,
                "type": col_type,
                "primary_key": bool(col.primary_key),
                "nullable": bool(col.nullable),
                "unique": bool(col.unique),
                "default": default_val
            })
            
            for fk in col.foreign_keys:
                foreign_keys.append({
                    "column": col.name,
                    "target_table": fk.column.table.name if hasattr(fk.column, 'table') else str(fk.target_fullname).split('.')[0],
                    "target_column": fk.column.name if hasattr(fk.column, 'name') else str(fk.target_fullname).split('.')[-1]
                })

        category, description = TABLE_CATEGORIES.get(table_name, ("General", "Database table"))
        table_rows = row_counts.get(table_name, 0)
        total_rows += table_rows

        tables_list.append({
            "table_name": table_name,
            "category": category,
            "description": description,
            "row_count": table_rows,
            "columns": columns,
            "foreign_keys": foreign_keys
        })

    # Sort tables alphabetically or by category
    category_order = ["Commerce & Sales", "Catalog & Inventory", "Customers & CRM", "Operations & System", "General"]
    tables_list.sort(key=lambda t: (category_order.index(t["category"]) if t["category"] in category_order else 99, t["table_name"]))

    categories = list(dict.fromkeys(t["category"] for t in tables_list))

    return {
        "total_tables": len(tables_list),
        "total_columns": total_columns,
        "total_rows": total_rows,
        "categories": categories,
        "tables": tables_list
    }

def get_schema_metadata() -> list[dict]:
    """
    Automatically extracts metadata from the SQLAlchemy Base metadata registry.
    Returns a list of dictionaries with 'table_name' and a textual representation 'schema_text'.
    """
    metadata = []
    
    for table_name, table in Base.metadata.tables.items():
        columns = []
        foreign_keys = []
        
        for col in table.columns:
            col_type = str(col.type)
            constraints = []
            if col.primary_key:
                constraints.append("PRIMARY KEY")
            if col.unique:
                constraints.append("UNIQUE")
            if not col.nullable:
                constraints.append("NOT NULL")
                
            constraints_str = " ".join(constraints)
            columns.append(f"{col.name} ({col_type}) {constraints_str}".strip())
            
            for fk in col.foreign_keys:
                foreign_keys.append(f"{col.name} -> {fk.target_fullname}")
        
        schema_text = f"Table: {table_name}\nColumns: " + ", ".join(columns)
        if foreign_keys:
            schema_text += "\nForeign Keys: " + ", ".join(foreign_keys)
            
        metadata.append({
            "table_name": table_name,
            "schema_text": schema_text
        })
        
    logger.info(f"Extracted metadata for {len(metadata)} tables.")
    return metadata

if __name__ == "__main__":
    md = get_schema_metadata()
    for m in md[:2]:
        print(m['schema_text'])
        print("-" * 40)
