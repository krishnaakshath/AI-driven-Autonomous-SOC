"""
 Structured Logger
====================
Centralized logging for all SOC services and pages.
Replaces print() calls and silent except: pass patterns.
"""

import logging
import sys
import uuid
import contextvars

# ═══════════════════════════════════════════════════════════════════════════════
# CORRELATION ID TRACING
# ═══════════════════════════════════════════════════════════════════════════════
correlation_id_var = contextvars.ContextVar('correlation_id', default='SYS-BOOT')

def get_correlation_id() -> str:
    return correlation_id_var.get()

def set_correlation_id(cid: str = None) -> str:
    """Initialize a new trace context. Returns the injected UUID."""
    if not cid:
        cid = f"REQ-{str(uuid.uuid4())[:8].upper()}"
    correlation_id_var.set(cid)
    return cid

class CorrelationIdFilter(logging.Filter):
    """Injects the current ContextVar Correlation ID into the log record dictionary."""
    def filter(self, record):
        record.correlation_id = correlation_id_var.get()
        return True

# ═══════════════════════════════════════════════════════════════════════════════
# ROOT LOGGER CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
_configured = False

def setup_logging(level=logging.INFO):
    """Configure structured, distributed, traceable logging for the SOC stack."""
    global _configured
    if _configured:
        return
    
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(correlation_id)s] [%(levelname)-7s] %(name)-15s | %(message)s",
        datefmt="%H:%M:%S"
    )
    
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIdFilter())
    
    root = logging.getLogger("soc")
    root.setLevel(level)
    root.addHandler(handler)
    root.addFilter(CorrelationIdFilter())
    root.propagate = False
    
    _configured = True

def get_logger(module_name: str) -> logging.Logger:
    """
    Get a named logger for a specific module, auto-wired with trace contexts.
    
    Usage:
        logger = get_logger("auth")
        logger.info("User logged in") # Emits: 14:22:11 [REQ-A1B2C3D4] [INFO] soc.auth | User logged in
    """
    setup_logging()
    return logging.getLogger(f"soc.{module_name}")
