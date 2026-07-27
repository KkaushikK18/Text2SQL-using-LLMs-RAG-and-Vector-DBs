from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "Enterprise Text-to-SQL"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///ecommerce.db"  # We will put it in the database dir
    
    # LLM Config
    GEMINI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "gemini-embedding-2"
    
    # Vector DB
    FAISS_INDEX_PATH: str = "embeddings/langchain_index"
    
    class Config:
        env_file = ".env"

settings = Settings()
