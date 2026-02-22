"""
Create Supabase tables for SOC database.
Run this ONCE to set up the events and alerts tables.
"""
import requests
import json

SUPABASE_URL = "https://rijcxktkydnbyiyhhcgq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJpamN4a3RreWRuYnlpeWhoY2dxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTc3MDgxMiwiZXhwIjoyMDg3MzQ2ODEyfQ.j-M8sfqZ5balakw4xd4SbjcspzKuoxVHk1V6PkjE8Hg"

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

# Use the Supabase SQL endpoint (via rpc or direct pg)
# PostgREST doesn't support DDL, so we use the /rest/v1/rpc endpoint
# Alternatively, we can try the pg endpoint

# Method 1: Try inserting a test record to see if tables exist
print("Testing Supabase connection...")
test_url = f"{SUPABASE_URL}/rest/v1/events"
r = requests.get(test_url, headers=headers, params={"limit": "1"})
print(f"Events table status: {r.status_code}")
if r.status_code == 200:
    print("Events table already exists!")
    print(f"Response: {r.json()}")
elif r.status_code == 404:
    print("Events table doesn't exist yet. Please create it via the Supabase SQL Editor.")
else:
    print(f"Unexpected response: {r.status_code} - {r.text}")

# Test alerts table
test_url2 = f"{SUPABASE_URL}/rest/v1/alerts"
r2 = requests.get(test_url2, headers=headers, params={"limit": "1"})
print(f"Alerts table status: {r2.status_code}")
if r2.status_code == 200:
    print("Alerts table already exists!")
elif r2.status_code == 404:
    print("Alerts table doesn't exist yet.")
else:
    print(f"Unexpected response: {r2.status_code} - {r2.text}")

print("\n--- COPY THE SQL BELOW INTO SUPABASE SQL EDITOR IF TABLES DON'T EXIST ---")
print(SQL)
"""
import json

SUPABASE_URL = "https://rijcxktkydnbyiyhhcgq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJpamN4a3RreWRuYnlpeWhoY2dxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTc3MDgxMiwiZXhwIjoyMDg3MzQ2ODEyfQ.j-M8sfqZ5balakw4xd4SbjcspzKuoxVHk1V6PkjE8Hg"
"""
