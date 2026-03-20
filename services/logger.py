"""
 Structured Logger
====================
Centralized logging for all SOC services and pages.
Replaces print() calls and silent except: pass patterns.
"""

import logging
import sys

# Configure the root SOC logger once
_configured = False

def setup_logging(level=logging.INFO):
    """Configure structured logging for the entire application."""
    global _configured
    if _configured:
        return
    
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-7s] %(name)-20s | %(message)s",
        datefmt="%H:%M:%S"
    )
    
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    
    root = logging.getLogger("soc")
    root.setLevel(level)
    root.addHandler(handler)
    root.propagate = False
    
    _configured = True


def get_logger(module_name: str) -> logging.Logger:
    """
    Get a named logger for a specific module.
    
    Usage:
        from services.logger import get_logger
        logger = get_logger("auth")
        logger.info("User logged in")
        logger.warning("Rate limit approaching")
        logger.exception("Unexpected failure")  # includes traceback
    """
    setup_logging()
    return logging.getLogger(f"soc.{module_name}")
