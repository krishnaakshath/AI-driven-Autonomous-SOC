"""
Database Service — Supabase (Cloud)
===================================
Uses Supabase PostgREST API for persistent cloud storage.
No external packages needed — uses built-in `requests`.
"""

import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional
from services.logger import get_logger
logger = get_logger("database")


# Load .env file if present (supports python-dotenv or manual parsing)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Manual .env parsing fallback
    _env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(_env_path):
        with open(_env_path) as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _key, _val = _line.split("=", 1)
                    os.environ.setdefault(_key.strip(), _val.strip())

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════
SUPABASE_URL = None
SUPABASE_KEY = None

# Try to load from environment, Streamlit secrets, or config file
try:
    import streamlit as st
    SUPABASE_URL = st.secrets.get("SUPABASE_URL")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
except Exception:

    logger.debug("Suppressed exception", exc_info=True)

if not SUPABASE_URL:
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL:
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".soc_config.json")
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
            SUPABASE_URL = config.get("SUPABASE_URL")
            SUPABASE_KEY = config.get("SUPABASE_KEY")
    except Exception:

        logger.debug("Suppressed exception", exc_info=True)


class SupabaseClient:
    """Lightweight Supabase PostgREST client using requests."""
    
    def __init__(self, url, key):
        self.url = url.rstrip("/")
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        self._connected = None
    
    def is_connected(self):
        """Test if Supabase is reachable."""
        if self._connected:
            return True
        try:
            r = requests.get(
                f"{self.url}/rest/v1/events?limit=1",
                headers=self.headers,
                timeout=5
            )
            self._connected = r.status_code in (200, 416)
            if self._connected:
                print(f"[DB] Supabase connected: {self.url}")
            else:
                print(f"[DB] Supabase returned {r.status_code}: {r.text[:200]}")
                self._connected = False
        except Exception as e:
            print(f"[DB] Supabase unreachable: {e}")
            self._connected = False
        return self._connected
    
    def insert(self, table, data):
        """Insert a row or list of rows, ignoring duplicates."""
        try:
            r = requests.post(
                f"{self.url}/rest/v1/{table}",
                headers={**self.headers, "Prefer": "return=minimal,resolution=ignore-duplicates"},
                json=data, # requests handles both dict and list of dicts properly
                timeout=15 # Increased timeout for potential bulk inserts
            )
            return r.status_code in (200, 201, 204, 409)
        except Exception as e:
            logger.warning("[DB] Supabase insert: %s", e)
            return False
    
    def select(self, table, params=None, limit=100, order="timestamp.desc"):
        """Select rows from a table."""
        try:
            query_params = params or {}
            query_params["limit"] = str(limit)
            query_params["order"] = order
            query_params["select"] = "*"
            
            r = requests.get(
                f"{self.url}/rest/v1/{table}",
                headers={**self.headers, "Prefer": "return=representation"},
                params=query_params,
                timeout=10
            )
            if r.status_code == 200:
                return r.json()
            return []
        except Exception as e:
            logger.warning("[DB] Supabase select: %s", e)
            return []
    
    def count(self, table, filters=None):
        """Count rows in a table."""
        try:
            headers = {**self.headers, "Prefer": "count=exact"}
            params = {"select": "*"}
            if filters:
                params.update(filters)
            
            r = requests.head(
                f"{self.url}/rest/v1/{table}",
                headers=headers,
                params=params,
                timeout=5
            )
            if r.status_code in (200, 204, 206):
                content_range = r.headers.get("content-range", "")
                if "/" in content_range:
                    return int(content_range.split("/")[-1])
            return 0
        except Exception as e:
            logger.warning("[DB] Supabase count: %s", e)
            return 0
    
    def search(self, table, query, columns, limit=50):
        """Search across multiple columns using OR."""
        try:
            or_clauses = ",".join([f"{col}.ilike.%25{query}%25" for col in columns])
            params = {
                "or": f"({or_clauses})",
                "limit": str(limit),
                "order": "timestamp.desc",
                "select": "*"
            }
            
            r = requests.get(
                f"{self.url}/rest/v1/{table}",
                headers={**self.headers, "Prefer": "return=representation"},
                params=params,
                timeout=10
            )
            if r.status_code == 200:
                return r.json()
            return []
        except Exception as e:
            logger.warning("[DB] Supabase search: %s", e)
            return []
    
    def rpc(self, function_name, params=None):
        """Call a Supabase RPC function."""
        try:
            r = requests.post(
                f"{self.url}/rest/v1/rpc/{function_name}",
                headers=self.headers,
                json=params or {},
                timeout=10
            )
            if r.status_code == 200:
                return r.json()
            return None
        except Exception:
            return None

    def update(self, table, filters, data):
        """Update rows matching filters with new data via PATCH."""
        try:
            params = filters or {}
            r = requests.patch(
                f"{self.url}/rest/v1/{table}",
                headers={**self.headers, "Prefer": "return=minimal"},
                params=params,
                json=data,
                timeout=10
            )
            return r.status_code in (200, 204)
        except Exception as e:
            logger.warning("[DB] Supabase update: %s", e)
            return False

    def delete_all(self, table):
        """Delete all rows from a table."""
        try:
            r = requests.delete(
                f"{self.url}/rest/v1/{table}",
                headers=self.headers,
                params={"timestamp": "not.is.IMPOSSIBLE"},
                timeout=10
            )
            return r.status_code in (200, 204)
        except Exception:
            return False


class DatabaseService:
    """Cloud database using Supabase PostgREST API exclusively."""
    
    def __init__(self):
        self._supabase = None
        
        if SUPABASE_URL and SUPABASE_KEY:
            self._supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
        
        if not self._use_supabase:
            print("[DB] CRITICAL WARNING: Supabase is unreachable. Cloud database is required.")

    @property
    def _use_supabase(self):
        if self._supabase:
            return self._supabase.is_connected()
        return False

    # ═══════════════════════════════════════════════════════════════════════════
    # INSERT METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def insert_event(self, event_data):
        """Insert a single event."""
        if not self._use_supabase: return
        row = {
            "id": event_data.get("id"),
            "timestamp": event_data.get("timestamp"),
            "source": event_data.get("source"),
            "event_type": event_data.get("event_type"),
            "severity": event_data.get("severity"),
            "source_ip": event_data.get("source_ip"),
            "dest_ip": event_data.get("dest_ip"),
            "user": event_data.get("user"),
            "status": event_data.get("status", "Open"),
            "raw_log": event_data  # JSONB in Supabase
        }
        self._supabase.insert("events", row)

    def insert_alert(self, alert_data):
        """Insert a generated alert."""
        if not self._use_supabase: return
        row = {
            "id": alert_data.get("id"),
            "timestamp": alert_data.get("timestamp"),
            "title": alert_data.get("title"),
            "severity": alert_data.get("severity"),
            "status": alert_data.get("status"),
            "details": alert_data  # JSONB in Supabase
        }
        self._supabase.insert("alerts", row)

    # ═══════════════════════════════════════════════════════════════════════════
    # SELECT METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_recent_events(self, limit=100):
        """Retrieve most recent events."""
        if not self._use_supabase: return []
        rows = self._supabase.select("events", limit=limit, order="timestamp.desc")
        results = []
        for row in rows:
            d = dict(row)
            if d.get("raw_log") and isinstance(d["raw_log"], dict):
                d.update(d["raw_log"])
            results.append(d)
        return results
    
    def get_alerts(self, limit=50):
        """Retrieve recent alerts."""
        if not self._use_supabase: return []
        return self._supabase.select("alerts", limit=limit, order="timestamp.desc")
    
    def search_events(self, query, limit=50):
        """Search events for a keyword."""
        if not self._use_supabase: return []
        return self._supabase.search(
            "events", query, 
            ["source_ip", "dest_ip", "user", "event_type"],
            limit=limit
        )

    def update_alert_status(self, alert_id, new_status):
        """Update the status of an alert by ID."""
        if not self._use_supabase:
            logger.warning("[DB] Cannot update alert — Supabase not connected")
            return False
        return self._supabase.update(
            "alerts",
            {"id": f"eq.{alert_id}"},
            {"status": new_status}
        )

    def update_event_status(self, event_id, new_status):
        """Update the status of an event by ID."""
        if not self._use_supabase:
            logger.warning("[DB] Cannot update event — Supabase not connected")
            return False
        return self._supabase.update(
            "events",
            {"id": f"eq.{event_id}"},
            {"status": new_status}
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # STATS METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_stats(self):
        """Get quick counts for dashboard."""
        if not self._use_supabase: return {"total": 0, "critical": 0, "high": 0}
        total = self._supabase.count("events")
        critical = self._supabase.count("events", {"severity": "eq.CRITICAL"})
        high = self._supabase.count("events", {"severity": "eq.HIGH"})
        return {"total": total, "critical": critical, "high": high}

    def get_daily_counts(self, days=30):
        """Get exact event counts grouped by day, bypassing row limits."""
        if not self._use_supabase: return []
        import concurrent.futures
        from datetime import timedelta
        
        day_counts = {}
        today = datetime.now()
        days_list = [(today - timedelta(days=d)).strftime("%Y-%m-%d") for d in range(days)]
        
        def fetch_day_count(d_str):
            next_day = (datetime.strptime(d_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            filters = {"and": f"(timestamp.gte.{d_str} 00:00:00,timestamp.lt.{next_day} 00:00:00)"}
            return d_str, self._supabase.count("events", filters)
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            for d_str, count in executor.map(fetch_day_count, days_list):
                day_counts[d_str] = count
                
        return [{"date": k, "count": v} for k, v in sorted(day_counts.items())]

    def get_monthly_counts(self):
        """Get exact event counts grouped by month, bypassing row limits."""
        if not self._use_supabase: return []
        import concurrent.futures
        from datetime import timedelta
        import calendar
        
        month_counts = {}
        today = datetime.now()
        months_list = sorted(list(set([(today - timedelta(days=d)).strftime("%Y-%m") for d in range(365)])))[-12:]
        
        def fetch_month_count(m_str):
            y, m = m_str.split('-')
            last_day = calendar.monthrange(int(y), int(m))[1]
            start_str = f"{m_str}-01 00:00:00"
            if int(m) == 12:
                next_month_str = f"{int(y)+1}-01-01 00:00:00"
            else:
                next_month_str = f"{y}-{int(m)+1:02d}-01 00:00:00"
                
            filters = {"and": f"(timestamp.gte.{start_str},timestamp.lt.{next_month_str})"}
            return m_str, self._supabase.count("events", filters)
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            for m_str, count in executor.map(fetch_month_count, months_list):
                month_counts[m_str] = count
                
        return [{"month": k, "count": v} for k, v in sorted(month_counts.items())]

    def get_threat_categories(self):
        """Get counts of high-severity event types."""
        if not self._use_supabase: return []
        rows = self._supabase.select(
            "events",
            params={"severity": "in.(HIGH,CRITICAL)", "select": "event_type"},
            limit=5000,
            order="timestamp.desc"
        )
        cat_counts = {}
        for row in rows:
            et = row.get("event_type", "Unknown")
            cat_counts[et] = cat_counts.get(et, 0) + 1
        sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:6]
        return [{"category": k, "count": v} for k, v in sorted_cats]

    def get_kpi_stats(self):
        """Get counts for Executive KPIs."""
        if not self._use_supabase: return {"resolved_alerts": 0, "false_positives": 0, "total_alerts": 0}
        resolved = self._supabase.count("alerts", {"status": "in.(Resolved,Contained)"})
        false_positives = self._supabase.count("events", {"status": "eq.False Positive"})
        total_alerts = self._supabase.count("alerts")
        return {
            "resolved_alerts": resolved,
            "false_positives": false_positives,
            "total_alerts": total_alerts
        }

    def clear_all(self, confirm: bool = False):
        """Clear all data."""
        if not confirm:
            print("[DATABASE] WARNING: clear_all() called without confirm=True. Data NOT deleted.")
            return
        if self._use_supabase:
            self._supabase.delete_all("events")
            self._supabase.delete_all("alerts")
            print("[DATABASE] All Supabase data cleared.")

    def get_all_events(self) -> list:
        """Retrieve ALL events for ML training."""
        if not self._use_supabase: return []
        rows = self._supabase.select("events", limit=20000, order="timestamp.asc")
        results = []
        for row in rows:
            d = dict(row)
            if d.get("raw_log") and isinstance(d["raw_log"], dict):
                d.update(d["raw_log"])
            results.append(d)
        return results

    def bulk_insert_alerts(self, alerts: List[Dict]) -> bool:
        """Insert multiple alerts optimally."""
        if not alerts or not self._use_supabase: return True
        success = True
        chunk_size = 1000
        for i in range(0, len(alerts), chunk_size):
            chunk = alerts[i:i + chunk_size]
            formatted_chunk = []
            for a in chunk:
                formatted_chunk.append({
                    "id": a.get("id"),
                    "timestamp": a.get("timestamp"),
                    "title": a.get("title"),
                    "severity": a.get("severity"),
                    "status": a.get("status"),
                    "details": a  # JSONB
                })
            if not self._supabase.insert("alerts", formatted_chunk):
                success = False
        return success
        
    def bulk_insert_events(self, events: List[Dict]) -> bool:
        """Insert multiple events optimally."""
        if not events or not self._use_supabase: return True
        success = True
        chunk_size = 1000
        for i in range(0, len(events), chunk_size):
            chunk = events[i:i + chunk_size]
            if not self._supabase.insert("events", chunk):
                success = False
                print(f"[DB] Failed to insert chunk {i // chunk_size} to Supabase")
        return success

    def get_event_count(self) -> int:
        """Fast event count."""
        if not self._use_supabase: return 0
        return self._supabase.count("events")

    def mass_seed_supabase(self, target_count: int = 180000):
        """Massive simulation backfill up to `target_count` using chunked batches."""
        if not self._use_supabase: return False
        print(f"[DB] Starting mass seed to reach {target_count} events...")
        try:
            from services.siem_service import siem_service
            
            current = self.get_event_count()
            if current >= target_count:
                print(f"[DB] Already at {current} events. No seed needed.")
                return True
                
            needed = target_count - current
            print(f"[DB] Currently at {current}. Generating {needed} new events in batches of 2000...")
            
            for i in range(0, needed, 2000):
                batch_size = min(2000, needed - i)
                events = siem_service.simulate_ingestion(count=batch_size)
                
                if self.bulk_insert_events(events):
                    print(f"[DB] Mass seed: Inserted {i + batch_size}/{needed} events")
                else:
                    logger.warning("[DB] Mass seed failed: %s", needed)
                    return False
            
            print("[DB] Mass seed complete.")
            return True
        except Exception as e:
            logger.warning("[DB] Mass seed: %s", e)
            return False

# Singleton instance
db = DatabaseService()
