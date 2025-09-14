"""Logging utilities for the ETL pipeline."""

import logging
import sys
from pathlib import Path


def setup_logger(name: str, output_dir: Path, level: str = "INFO") -> logging.Logger:
    """Setup logger with console and file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logger.level)
    console_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    output_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(output_dir / "pipeline.log", encoding="utf-8")
    file_handler.setLevel(logger.level)
    file_handler.setFormatter(console_formatter)
    logger.addHandler(file_handler)
    
    return logger