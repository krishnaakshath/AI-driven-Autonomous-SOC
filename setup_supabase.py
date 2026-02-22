"""
Create Supabase tables for SOC database.
Run this ONCE to set up the events and alerts tables.

Usage:
  1. Set SUPABASE_URL and SUPABASE_KEY as environment variables, or
  2. They will be read from .soc_config.json

Then run: python setup_supabase.py
"""
import os
import json
import requests

# Load credentials from environment or config file
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL:
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".soc_config.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
            SUPABASE_URL = config.get("SUPABASE_URL", "")
            SUPABASE_KEY = config.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set.")
    print("Set them as environment variables or in .soc_config.json")
    exit(1)

# SQL to create tables
SQL = """
CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  timestamp TIMESTAMPTZ,
  source TEXT,
  event_type TEXT,
  severity TEXT,
  source_ip TEXT,
  dest_ip TEXT,
  "user" TEXT,
  status TEXT DEFAULT 'Open',
  raw_log JSONB
);

CREATE TABLE IF NOT EXISTS alerts (
  id TEXT PRIMARY KEY,
  timestamp TIMESTAMPTZ,
  title TEXT,
  severity TEXT,
  status TEXT,
  details JSONB
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_severity ON events(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp DESC);
"""

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Test if tables exist
print("Testing Supabase connection...")
test_url = f"{SUPABASE_URL}/rest/v1/events"
r = requests.get(test_url, headers=headers, params={"limit": "1"})
print(f"Events table status: {r.status_code}")
if r.status_code == 200:
    print("✅ Events table already exists!")
    print(f"Response: {r.json()}")
elif r.status_code == 404:
    print("❌ Events table doesn't exist yet. Please create it via the Supabase SQL Editor.")
else:
    print(f"⚠️  Unexpected response: {r.status_code} - {r.text}")

# Test alerts table
test_url2 = f"{SUPABASE_URL}/rest/v1/alerts"
r2 = requests.get(test_url2, headers=headers, params={"limit": "1"})
print(f"Alerts table status: {r2.status_code}")
if r2.status_code == 200:
    print("✅ Alerts table already exists!")
elif r2.status_code == 404:
    print("❌ Alerts table doesn't exist yet.")
else:
    print(f"⚠️  Unexpected response: {r2.status_code} - {r2.text}")

print("\n--- COPY THE SQL BELOW INTO SUPABASE SQL EDITOR IF TABLES DON'T EXIST ---")
print(SQL)
