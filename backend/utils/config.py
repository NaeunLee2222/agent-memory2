# import os
# from dotenv import load_dotenv

# load_dotenv()


# class Config:
#     OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
#     MEM0_API_KEY = os.getenv("MEM0_API_KEY")
#     REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380")
#     CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
#     CHROMA_PORT = os.getenv("CHROMA_PORT", "8001")
#     NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
#     NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
#     NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "testpassword")
#     ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
#     LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# config = Config()
import os
from typing import Dict, Any
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # ChromaDB Configuration
    CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    
    # Neo4j Configuration
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # MongoDB Configuration
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "procedural_memory")
    
    # MCP Server Configuration
    MCP_SERVER_URL: str = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
    MCP_TIMEOUT: float = float(os.getenv("MCP_TIMEOUT", "30.0"))
    
    # OpenAI Configuration (if used)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Application Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    class Config:
        env_file = ".env"

settings = Settings()