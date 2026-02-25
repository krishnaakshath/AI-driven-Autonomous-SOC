"""
Database Service — Supabase (Cloud) + SQLite (Local Fallback)
=============================================================
Uses Supabase PostgREST API for persistent cloud storage.
Falls back to SQLite for local development when Supabase is unreachable.
No external packages needed — uses built-in `requests`.
"""

import sqlite3
import json
import os
import threading
import requests
from datetime import datetime
from typing import Dict, List, Optional

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
    pass

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
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# SQLite FALLBACK (for local dev)
# ═══════════════════════════════════════════════════════════════════════════════
DB_PATH = "soc_data.db"
_db_lock = threading.Lock()


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
        if self._connected is not None:
            return self._connected
        try:
            r = requests.get(
                f"{self.url}/rest/v1/events?limit=1",
                headers=self.headers,
                timeout=5
            )
            self._connected = r.status_code in (200, 416)
            if self._connected:
                print(f"[DB] ✅ Supabase connected: {self.url}")
            else:
                print(f"[DB] ❌ Supabase returned {r.status_code}: {r.text[:200]}")
                self._connected = False
        except Exception as e:
            print(f"[DB] ❌ Supabase unreachable: {e}")
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
            print(f"[DB] Supabase insert error: {e}")
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
            print(f"[DB] Supabase select error: {e}")
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
            print(f"[DB] Supabase count error: {e}")
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
            print(f"[DB] Supabase search error: {e}")
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
    
    def delete_all(self, table):
        """Delete all rows from a table."""
        try:
            r = requests.delete(
                f"{self.url}/rest/v1/{table}",
                headers=self.headers,
                params={"id": "neq.IMPOSSIBLE_VALUE_THAT_MATCHES_ALL"},  # Delete all hack
                timeout=10
            )
            # Alternative: use a filter that matches everything
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
    """Dual-mode database: Supabase (cloud) with SQLite fallback (local)."""
    
    def __init__(self):
        self._supabase = None
        self._use_supabase = False
        
        # Try Supabase first
        if SUPABASE_URL and SUPABASE_KEY:
            self._supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
            try:
                self._use_supabase = self._supabase.is_connected()
            except Exception:
                self._use_supabase = False
        
        if not self._use_supabase:
            print("[DB] Using SQLite fallback (local mode)")
        
        # Always init SQLite as fallback
        self._init_sqlite()
    
    def _init_sqlite(self):
        """Initialize SQLite tables (fallback)."""
        with _db_lock:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            c = conn.cursor()
            
            c.execute('''CREATE TABLE IF NOT EXISTS events
                         (id TEXT PRIMARY KEY, timestamp TEXT, source TEXT, 
                          event_type TEXT, severity TEXT, source_ip TEXT, 
                          dest_ip TEXT, user TEXT, status TEXT, raw_log TEXT)''')
            
            c.execute("PRAGMA table_info(events)")
            columns = [col[1] for col in c.fetchall()]
            if 'status' not in columns:
                c.execute("ALTER TABLE events ADD COLUMN status TEXT DEFAULT 'Open'")
            
            c.execute('''CREATE TABLE IF NOT EXISTS alerts
                         (id TEXT PRIMARY KEY, timestamp TEXT, title TEXT, 
                          severity TEXT, status TEXT, details TEXT)''')
            
            conn.commit()
            conn.close()

    def _get_conn(self):
        return sqlite3.connect(DB_PATH, check_same_thread=False)

    # ═══════════════════════════════════════════════════════════════════════════
    # INSERT METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def insert_event(self, event_data):
        """Insert a single event."""
        if self._use_supabase:
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
        else:
            with _db_lock:
                conn = self._get_conn()
                c = conn.cursor()
                try:
                    c.execute('''INSERT OR IGNORE INTO events 
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (event_data.get('id'), event_data.get('timestamp'), 
                               event_data.get('source'), event_data.get('event_type'),
                               event_data.get('severity'), event_data.get('source_ip'), 
                               event_data.get('dest_ip'), event_data.get('user'),
                               event_data.get('status', 'Open'),
                               json.dumps(event_data)))
                    conn.commit()
                except Exception as e:
                    print(f"DB Error insert_event: {e}")
                finally:
                    conn.close()
    
    def insert_alert(self, alert_data):
        """Insert a generated alert."""
        if self._use_supabase:
            row = {
                "id": alert_data.get("id"),
                "timestamp": alert_data.get("timestamp"),
                "title": alert_data.get("title"),
                "severity": alert_data.get("severity"),
                "status": alert_data.get("status"),
                "details": alert_data  # JSONB in Supabase
            }
            self._supabase.insert("alerts", row)
        else:
            with _db_lock:
                conn = self._get_conn()
                c = conn.cursor()
                try:
                    c.execute('''INSERT OR IGNORE INTO alerts 
                                 VALUES (?, ?, ?, ?, ?, ?)''',
                              (alert_data.get('id'), alert_data.get('timestamp'), 
                               alert_data.get('title'), alert_data.get('severity'),
                               alert_data.get('status'), json.dumps(alert_data)))
                    conn.commit()
                except Exception as e:
                    print(f"DB Error insert_alert: {e}")
                finally:
                    conn.close()

    # ═══════════════════════════════════════════════════════════════════════════
    # SELECT METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_recent_events(self, limit=100):
        """Retrieve most recent events."""
        if self._use_supabase:
            rows = self._supabase.select("events", limit=limit, order="timestamp.desc")
            results = []
            for row in rows:
                d = dict(row)
                # Merge raw_log JSONB back into the dict
                if d.get("raw_log") and isinstance(d["raw_log"], dict):
                    d.update(d["raw_log"])
                results.append(d)
            return results
        else:
            with _db_lock:
                conn = self._get_conn()
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,))
                rows = c.fetchall()
                conn.close()
                
                results = []
                for row in rows:
                    d = dict(row)
                    try:
                        if d.get('raw_log'):
                            full_data = json.loads(d['raw_log'])
                            d.update(full_data)
                    except:
                        pass
                    results.append(d)
                return results
    
    def get_alerts(self, limit=50):
        """Retrieve recent alerts."""
        if self._use_supabase:
            rows = self._supabase.select("alerts", limit=limit, order="timestamp.desc")
            return rows
        else:
            with _db_lock:
                conn = self._get_conn()
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,))
                rows = c.fetchall()
                conn.close()
                return [dict(row) for row in rows]
    
    def search_events(self, query, limit=50):
        """Search events for a keyword."""
        if self._use_supabase:
            return self._supabase.search(
                "events", query, 
                ["source_ip", "dest_ip", "user", "event_type"],
                limit=limit
            )
        else:
            with _db_lock:
                conn = self._get_conn()
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                wildcard = f"%{query}%"
                c.execute("""
                    SELECT * FROM events 
                    WHERE source_ip LIKE ? 
                       OR dest_ip LIKE ? 
                       OR user LIKE ? 
                       OR event_type LIKE ? 
                       OR raw_log LIKE ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (wildcard, wildcard, wildcard, wildcard, wildcard, limit))
                rows = c.fetchall()
                conn.close()
                return [dict(row) for row in rows]

    # ═══════════════════════════════════════════════════════════════════════════
    # STATS METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_stats(self):
        """Get quick counts for dashboard."""
        if self._use_supabase:
            total = self._supabase.count("events")
            critical = self._supabase.count("events", {"severity": "eq.CRITICAL"})
            high = self._supabase.count("events", {"severity": "eq.HIGH"})
            return {"total": total, "critical": critical, "high": high}
        else:
            with _db_lock:
                conn = self._get_conn()
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM events")
                total = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM events WHERE severity='CRITICAL'")
                critical = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM events WHERE severity='HIGH'")
                high = c.fetchone()[0]
                conn.close()
                return {"total": total, "critical": critical, "high": high}

    def get_daily_counts(self, days=30):
        """Get event counts grouped by day."""
        if self._use_supabase:
            # Use Supabase select with date filtering
            from datetime import timedelta
            cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            rows = self._supabase.select(
                "events",
                params={"timestamp": f"gte.{cutoff}", "select": "timestamp"},
                limit=100000,
                order="timestamp.asc"
            )
            # Group by day in Python
            day_counts = {}
            for row in rows:
                ts = row.get("timestamp", "")[:10]
                day_counts[ts] = day_counts.get(ts, 0) + 1
            return [{"date": k, "count": v} for k, v in sorted(day_counts.items())]
        else:
            with _db_lock:
                conn = self._get_conn()
                c = conn.cursor()
                c.execute(f"""
                    SELECT date(timestamp) as day, COUNT(*) as count 
                    FROM events 
                    WHERE timestamp >= date('now', '-{int(days)} days')
                    GROUP BY day 
                    ORDER BY day ASC
                """)
                rows = c.fetchall()
                conn.close()
                return [{"date": row[0], "count": row[1]} for row in rows]

    def get_monthly_counts(self):
        """Get event counts grouped by month."""
        if self._use_supabase:
            from datetime import timedelta
            cutoff = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            rows = self._supabase.select(
                "events",
                params={"timestamp": f"gte.{cutoff}", "select": "timestamp"},
                limit=20000,
                order="timestamp.asc"
            )
            month_counts = {}
            for row in rows:
                month = row.get("timestamp", "")[:7]
                month_counts[month] = month_counts.get(month, 0) + 1
            return [{"month": k, "count": v} for k, v in sorted(month_counts.items())]
        else:
            with _db_lock:
                conn = self._get_conn()
                c = conn.cursor()
                c.execute("""
                    SELECT strftime('%Y-%m', timestamp) as month, COUNT(*) as count 
                    FROM events 
                    WHERE timestamp >= date('now', '-12 months')
                    GROUP BY month 
                    ORDER BY month ASC
                """)
                rows = c.fetchall()
                conn.close()
                return [{"month": row[0], "count": row[1]} for row in rows]

    def get_threat_categories(self):
        """Get counts of high-severity event types."""
        if self._use_supabase:
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
        else:
            with _db_lock:
                conn = self._get_conn()
                c = conn.cursor()
                c.execute("""
                    SELECT event_type, COUNT(*) as count 
                    FROM events 
                    WHERE severity IN ('HIGH', 'CRITICAL') 
                    GROUP BY event_type 
                    ORDER BY count DESC 
                    LIMIT 6
                """)
                rows = c.fetchall()
                conn.close()
                return [{"category": row[0], "count": row[1]} for row in rows]

    def get_kpi_stats(self):
        """Get counts for Executive KPIs."""
        if self._use_supabase:
            resolved = self._supabase.count("alerts", {"status": "in.(Resolved,Contained)"})
            false_positives = self._supabase.count("events", {"status": "eq.False Positive"})
            total_alerts = self._supabase.count("alerts")
            return {
                "resolved_alerts": resolved,
                "false_positives": false_positives,
                "total_alerts": total_alerts
            }
        else:
            with _db_lock:
                conn = self._get_conn()
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM alerts WHERE status IN ('Resolved', 'Contained')")
                resolved = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM events WHERE status='False Positive'")
                false_positives = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM alerts")
                total_alerts = c.fetchone()[0]
                conn.close()
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
        else:
            with _db_lock:
                conn = self._get_conn()
                c = conn.cursor()
                c.execute("DELETE FROM events")
                c.execute("DELETE FROM alerts")
                conn.commit()
                conn.close()
                print("[DATABASE] All SQLite data cleared.")

    def get_all_events(self) -> list:
        """Retrieve ALL events for ML training."""
        if self._use_supabase:
            rows = self._supabase.select("events", limit=20000, order="timestamp.asc")
            results = []
            for row in rows:
                d = dict(row)
                if d.get("raw_log") and isinstance(d["raw_log"], dict):
                    d.update(d["raw_log"])
                results.append(d)
            return results
        else:
            with _db_lock:
                conn = self._get_conn()
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("SELECT * FROM events ORDER BY timestamp ASC")
                rows = c.fetchall()
                conn.close()
                
                results = []
                for row in rows:
                    d = dict(row)
                    try:
                        if d.get('raw_log'):
                            full_data = json.loads(d['raw_log'])
                            d.update(full_data)
                    except:
                        pass
                    results.append(d)
                return results

    def insert_event(self, event: Dict) -> bool:
        """Insert a single event."""
        if self._use_supabase:
            return self._supabase.insert("events", event)
        return self._insert_sqlite("events", event)
        
    def bulk_insert_alerts(self, alerts: List[Dict]) -> bool:
        """Insert multiple alerts optimally."""
        if not alerts:
            return True
            
        if self._use_supabase:
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
        return True
        
    def bulk_insert_events(self, events: List[Dict]) -> bool:
        """Insert multiple events optimally."""
        if not events:
            return True
            
        if self._use_supabase:
            # Batch in chunks of 1000 to avoid request size limits
            success = True
            chunk_size = 1000
            for i in range(0, len(events), chunk_size):
                chunk = events[i:i + chunk_size]
                if not self._supabase.insert("events", chunk):
                    success = False
                    print(f"[DB] Failed to insert chunk {i // chunk_size} to Supabase")
            return success
            
        # SQLite Fallback: Execute many
        try:
            with sqlite3.connect(self._sqlite_path) as conn:
                cursor = conn.cursor()
                keys = "id, timestamp, source, event_type, severity, source_ip, dest_ip, user, hostname, status, details, raw_log, ml_anomaly_score, ml_classification"
                placeholders = ",".join(["?"] * 14)
                
                rows = []
                for e in events:
                    rows.append((
                        e.get("id"), e.get("timestamp"), e.get("source"),
                        e.get("event_type"), e.get("severity"), e.get("source_ip"),
                        e.get("dest_ip"), e.get("user"), e.get("hostname"),
                        e.get("status"), e.get("details"), e.get("raw_log"),
                        e.get("ml_anomaly_score"), e.get("ml_classification")
                    ))
                    
                cursor.executemany(
                    f"INSERT OR IGNORE INTO events ({keys}) VALUES ({placeholders})",
                    rows
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"[DB] SQLite bulk insert error: {e}")
            return False

    def get_event_count(self) -> int:
        """Fast event count."""
        if self._use_supabase:
            return self._supabase.count("events")
        else:
            with _db_lock:
                conn = self._get_conn()
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM events")
                count = c.fetchone()[0]
                conn.close()
                return count

    def mass_seed_supabase(self, target_count: int = 180000):
        """Massive simulation backfill up to `target_count` using chunked batches."""
        print(f"[DB] Starting mass seed to reach {target_count} events...")
        try:
            from services.siem_service import siem_service
            
            current = self.get_event_count()
            if current >= target_count:
                print(f"[DB] Already at {current} events. No seed needed.")
                return True
                
            needed = target_count - current
            print(f"[DB] Currently at {current}. Generating {needed} new events in batches of 2000...")
            
            # Generate in chunks of 2000 to prevent local memory issues
            for i in range(0, needed, 2000):
                batch_size = min(2000, needed - i)
                events = siem_service.simulate_ingestion(count=batch_size)
                
                # Bulk insert handles the 200-row Supabase chunking internally
                if self.bulk_insert_events(events):
                    print(f"[DB] Mass seed: Inserted {i + batch_size}/{needed} events")
                else:
                    print(f"[DB] Mass seed failed at {i + batch_size}/{needed}")
                    return False
            
            print("[DB] Mass seed complete.")
            return True
        except Exception as e:
            print(f"[DB] Mass seed error: {e}")
            return False

# Singleton instance
db = DatabaseService()
