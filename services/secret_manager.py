"""
 Secure Secret Manager
========================
Centralized secret management for the SOC platform.

Priority order for reading secrets:
1. Streamlit secrets  (st.secrets — encrypted by Streamlit Cloud)
2. Environment variables  (os.environ)
3. Encrypted config file  (.soc_config.enc — Fernet AES-128)
4. Plain-text fallback     (.soc_config.json — local dev only)

NEVER log or display full secret values.
"""

import os
import json
import hashlib
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────────
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG_PLAIN = os.path.join(_PROJECT_ROOT, '.soc_config.json')
_CONFIG_ENCRYPTED = os.path.join(_PROJECT_ROOT, '.soc_config.enc')
_KEY_FILE = os.path.join(_PROJECT_ROOT, 'data', '.secret_key')


# ── Encryption helpers ───────────────────────────────────────────────────────
def _get_fernet():
    """Get a Fernet instance for encrypting/decrypting the config file."""
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        return None

    # Derive or load encryption key
    key = os.environ.get('SOC_SECRET_KEY')
    if key:
        # Use env var directly (should be URL-safe base64 Fernet key)
        return Fernet(key.encode())

    # Fall back to file-based key
    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, 'rb') as f:
            key_bytes = f.read().strip()
        return Fernet(key_bytes)

    # Generate and save a new key (first-run only)
    try:
        key_bytes = Fernet.generate_key()
        os.makedirs(os.path.dirname(_KEY_FILE), exist_ok=True)
        with open(_KEY_FILE, 'wb') as f:
            f.write(key_bytes)
        os.chmod(_KEY_FILE, 0o600)  # Owner-read only
        return Fernet(key_bytes)
    except Exception as e:
        logger.warning(f"Cannot create encryption key: {e}")
        return None


def _load_encrypted_config() -> Dict:
    """Load and decrypt the encrypted config file."""
    fernet = _get_fernet()
    if not fernet or not os.path.exists(_CONFIG_ENCRYPTED):
        return {}
    try:
        with open(_CONFIG_ENCRYPTED, 'rb') as f:
            encrypted = f.read()
        decrypted = fernet.decrypt(encrypted)
        return json.loads(decrypted.decode('utf-8'))
    except Exception as e:
        logger.warning(f"Failed to decrypt config: {e}")
        return {}


def _save_encrypted_config(data: Dict):
    """Encrypt and save config to the encrypted file."""
    fernet = _get_fernet()
    if not fernet:
        logger.warning("No encryption available; cannot save encrypted config")
        return False
    try:
        plaintext = json.dumps(data, indent=2).encode('utf-8')
        encrypted = fernet.encrypt(plaintext)
        with open(_CONFIG_ENCRYPTED, 'wb') as f:
            f.write(encrypted)
        return True
    except Exception as e:
        logger.error(f"Failed to save encrypted config: {e}")
        return False


def _load_plain_config() -> Dict:
    """Load the plain-text config (local dev fallback)."""
    if os.path.exists(_CONFIG_PLAIN):
        try:
            with open(_CONFIG_PLAIN, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


# ── Public API ───────────────────────────────────────────────────────────────

def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve a secret by key, checking sources in priority order:
    1. Streamlit secrets  (st.secrets)
    2. Environment variables
    3. Encrypted config file
    4. Plain-text config file (local dev)
    """
    # 1. Streamlit secrets
    try:
        import streamlit as st
        value = st.secrets.get(key)
        if value:
            return str(value)
    except Exception:
        pass

    # 2. Environment variables (also check UPPER_CASE variant)
    value = os.environ.get(key) or os.environ.get(key.upper())
    if value:
        return value

    # 3. Encrypted config
    enc_config = _load_encrypted_config()
    if key in enc_config:
        return str(enc_config[key])

    # 4. Plain-text config (dev fallback)
    plain_config = _load_plain_config()
    if key in plain_config:
        return str(plain_config[key])

    return default


def set_secret(key: str, value: str) -> bool:
    """
    Store a secret. Saves to encrypted config file.
    Also updates plain-text config for backward compatibility.
    """
    # Update encrypted config
    enc_config = _load_encrypted_config()
    enc_config[key] = value
    encrypted_ok = _save_encrypted_config(enc_config)

    # Also update plain config for backward compat with services
    plain_config = _load_plain_config()
    plain_config[key] = value
    try:
        with open(_CONFIG_PLAIN, 'w') as f:
            json.dump(plain_config, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to update plain config: {e}")

    return encrypted_ok


def delete_secret(key: str) -> bool:
    """Remove a secret from all config stores."""
    removed = False

    enc_config = _load_encrypted_config()
    if key in enc_config:
        del enc_config[key]
        _save_encrypted_config(enc_config)
        removed = True

    plain_config = _load_plain_config()
    if key in plain_config:
        del plain_config[key]
        try:
            with open(_CONFIG_PLAIN, 'w') as f:
                json.dump(plain_config, f, indent=2)
        except Exception:
            pass
        removed = True

    return removed


def list_secrets() -> List[Dict]:
    """
    List all known secret keys with masked values.
    Returns list of {key, masked_value, source} dicts.
    """
    seen = {}

    # Plain config (lowest priority — added first, overridden later)
    for k, v in _load_plain_config().items():
        seen[k] = {'key': k, 'masked_value': mask_secret(str(v)), 'source': 'config_file'}

    # Encrypted config
    for k, v in _load_encrypted_config().items():
        seen[k] = {'key': k, 'masked_value': mask_secret(str(v)), 'source': 'encrypted'}

    # Environment variables (check known keys)
    known_env_keys = [
        'GMAIL_USER', 'GMAIL_APP_PASSWORD', 'GEMINI_API_KEY',
        'VIRUSTOTAL_API_KEY', 'ABUSEIPDB_API_KEY', 'OTX_API_KEY',
        'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID', 'SOC_SECRET_KEY',
    ]
    for k in known_env_keys:
        v = os.environ.get(k)
        if v:
            seen[k.lower()] = {'key': k.lower(), 'masked_value': mask_secret(v), 'source': 'env_var'}

    # Streamlit secrets
    try:
        import streamlit as st
        for k in st.secrets:
            v = str(st.secrets[k])
            seen[k] = {'key': k, 'masked_value': mask_secret(v), 'source': 'streamlit'}
    except Exception:
        pass

    return list(seen.values())


def mask_secret(value: str) -> str:
    """
    Mask a secret value for display: show only last 4 characters.
    Examples:
        'my_long_api_key_12345'  →  '••••••••••••••••2345'
        'short'                   →  '•hort'
        ''                        →  '••••'
    """
    if not value:
        return '••••'
    if len(value) <= 4:
        return '•' * (len(value) - 1) + value[-1]
    return '•' * (len(value) - 4) + value[-4:]


def rotate_secret(key: str, new_value: str) -> bool:
    """
    Rotate a secret: replace the old value with a new one.
    Logs the rotation event (without values) for audit.
    """
    old_exists = get_secret(key) is not None
    success = set_secret(key, new_value)
    if success:
        _log_audit_event('secret_rotated', {
            'key': key,
            'was_existing': old_exists,
        })
    return success


def _log_audit_event(event_type: str, details: Dict):
    """Append an audit event to the audit log file."""
    from datetime import datetime
    audit_file = os.path.join(_PROJECT_ROOT, 'data', 'audit_log.json')
    try:
        if os.path.exists(audit_file):
            with open(audit_file, 'r') as f:
                log = json.load(f)
        else:
            log = []

        log.append({
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'details': details,
        })

        # Keep last 1000 entries
        log = log[-1000:]

        os.makedirs(os.path.dirname(audit_file), exist_ok=True)
        with open(audit_file, 'w') as f:
            json.dump(log, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to write audit log: {e}")


def encrypt_existing_config():
    """
    One-time migration: encrypt the existing plain-text config.
    Call this once to create the .soc_config.enc file.
    """
    plain = _load_plain_config()
    if not plain:
        print("No plain config found to encrypt.")
        return False
    success = _save_encrypted_config(plain)
    if success:
        print(f"Encrypted {len(plain)} secrets to {_CONFIG_ENCRYPTED}")
    return success
