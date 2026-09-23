from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()  # actually reads .env into environment — was missing before


class Settings(BaseSettings):
    # API Keys — only Groq needed now, free tier: https://console.groq.com
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Vector DB
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION: str = "claim_evidence"

    # LLM Config (Groq, free)
    LLM_MODEL: str = "openai/gpt-oss-20b"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # local sentence-transformers, no API

    # Verification Thresholds
    SUPPORTED_THRESHOLD: float = 0.75
    REFUTED_THRESHOLD: float = 0.25

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True


settings = Settings()
