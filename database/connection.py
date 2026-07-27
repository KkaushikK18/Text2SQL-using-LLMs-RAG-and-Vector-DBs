import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import settings
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Ensure database directory exists
db_dir = os.path.dirname(os.path.dirname(__file__)) + "/database"
db_path = f"sqlite:///{os.path.join(db_dir, 'ecommerce_v2.db')}"

# If settings has a specific sqlite db we can override, but let's use a new v2 DB
engine = create_engine(db_path, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Dependency to get a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
