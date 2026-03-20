"""
Environment Validation
========================
Validates required environment variables at startup.
Provides explicit diagnostics for missing keys.
"""

import os
import sys
from services.logger import get_logger

logger = get_logger("env")

# Required secrets with descriptions
REQUIRED_SECRETS = {
    "SUPABASE_URL": "Supabase project URL (e.g., https://xxx.supabase.co)",
    "SUPABASE_KEY": "Supabase service role key",
}

OPTIONAL_SECRETS = {
    "ABUSEIPDB_API_KEY": "AbuseIPDB API key for IP reputation checks",
    "OTX_API_KEY": "AlienVault OTX API key for threat intelligence",
    "VIRUSTOTAL_API_KEY": "VirusTotal API key for file/URL scanning",
    "GOOGLE_CLIENT_ID": "Google OAuth client ID",
    "GOOGLE_CLIENT_SECRET": "Google OAuth client secret",
    "TELEGRAM_BOT_TOKEN": "Telegram bot token for alert notifications",
    "TELEGRAM_CHAT_ID": "Telegram chat ID for alerts",
    "GEMINI_API_KEY": "Google Gemini API key for AI assistant",
    "OPENAI_API_KEY": "OpenAI API key for AI assistant",
}


def _get_secret(key: str) -> str | None:
    """Get a secret from Streamlit secrets or environment variables."""
    # Try Streamlit secrets first
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val:
            return str(val)
    except Exception:
        pass
    # Fallback to environment
    return os.environ.get(key)


def validate_environment(strict: bool = False) -> dict:
    """
    Validate all required and optional environment variables.
    
    Args:
        strict: If True, raise SystemExit on missing required keys.
    
    Returns:
        dict with keys: missing_required, missing_optional, available
    """
    result = {
        "missing_required": [],
        "missing_optional": [],
        "available": [],
    }

    for key, desc in REQUIRED_SECRETS.items():
        if _get_secret(key):
            result["available"].append(key)
        else:
            result["missing_required"].append((key, desc))
            logger.warning("Missing required secret: %s — %s", key, desc)

    for key, desc in OPTIONAL_SECRETS.items():
        if _get_secret(key):
            result["available"].append(key)
        else:
            result["missing_optional"].append((key, desc))
            logger.debug("Optional secret not set: %s", key)

    if result["missing_required"]:
        msg = "Missing required environment variables:\n"
        for key, desc in result["missing_required"]:
            msg += f"  - {key}: {desc}\n"
        logger.error(msg)
        if strict:
            print(f"\n{'='*60}\n STARTUP ERROR: {msg}{'='*60}\n", file=sys.stderr)
            sys.exit(1)
    else:
        logger.info("All required environment variables are set (%d available)", len(result["available"]))

    return result


def get_env_status_summary() -> str:
    """Return a human-readable summary for the Settings page."""
    result = validate_environment(strict=False)
    lines = []
    if result["available"]:
        lines.append(f"Configured: {', '.join(result['available'])}")
    if result["missing_required"]:
        lines.append(f"MISSING (required): {', '.join(k for k, _ in result['missing_required'])}")
    if result["missing_optional"]:
        lines.append(f"Not set (optional): {', '.join(k for k, _ in result['missing_optional'])}")
    return "\n".join(lines)
