"""Logging utilities for the Visual Constraint Discovery system."""

from loguru import logger
from pathlib import Path
from typing import Optional
import sys


def setup_logging(log_dir: Optional[Path] = None, log_level: str = "INFO", name: str = "vlm_puzzle") -> None:
    """
    Configure logging for the entire system.

    Args:
        log_dir: Directory to save log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        name: Name of the logger
    """
    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stdout,
        level=log_level,
        format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # Add file handler if log_dir provided
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{name}.log"
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            rotation="500 MB",
        )


def get_logger(name: str):
    """Get logger instance with given name."""
    return logger.bind(name=name)
