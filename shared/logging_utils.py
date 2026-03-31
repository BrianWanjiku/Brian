# jarvis/shared/logging_utils.py
"""Structured logger with timestamps and module-level prefixes."""

import logging
import sys
from shared.config import LOG_LEVEL

_FMT = "%(asctime)s │ %(name)-22s │ %(levelname)-7s │ %(message)s"
_DATE_FMT = "%H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger scoped to *name* (e.g. 'orchestrator')."""
    logger = logging.getLogger(f"jarvis.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_FMT, datefmt=_DATE_FMT))
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    return logger
