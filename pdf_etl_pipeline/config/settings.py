"""Configuration settings for the PDF ETL pipeline."""

from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Pipeline configuration settings."""
    
    # Model settings
    VLM_MODEL: str = os.getenv("VLM_MODEL", "gpt-4o")
    
    # Processing settings
    DPI: int = int(os.getenv("DPI", "200"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Default paths
    DEFAULT_INPUT_DIR = Path("data/input")
    DEFAULT_OUTPUT_DIR = Path("data/output")
    
    @classmethod
    def validate(cls) -> None:
        """Validate required settings."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")


# Global settings instance
settings = Settings()