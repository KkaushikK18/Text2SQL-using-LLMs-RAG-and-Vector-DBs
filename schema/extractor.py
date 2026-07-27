import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.models import Base
from utils.logger import get_logger

logger = get_logger("SchemaExtractor")

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
