import sqlite3
import json
from datetime import datetime
import os
import threading

# Use a thread-local storage for connections to avoid check_same_thread issues
# while still being safe. However, streamlit re-runs scripts so a global connection
# might be tricky. Best practice for sqlite in streamlit is enabling check_same_thread=False
# if we are careful, or opening a new connection per request. 
# We'll use check_same_thread=False for simplicity in this project, but with a lock.

DB_PATH = "soc_data.db"
_db_lock = threading.Lock()

class DatabaseService:
    def __init__(self):
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(DB_PATH, check_same_thread=False)

    def _init_db(self):
        """Initialize tables if they don't exist."""
        with _db_lock:
            conn = self._get_conn()
            c = conn.cursor()
            
            # Events Table
            c.execute('''CREATE TABLE IF NOT EXISTS events
                         (id TEXT PRIMARY KEY, timestamp TEXT, source TEXT, 
                          event_type TEXT, severity TEXT, source_ip TEXT, 
                          dest_ip TEXT, user TEXT, status TEXT, raw_log TEXT)''')
            
            # Alerts Table
            c.execute('''CREATE TABLE IF NOT EXISTS alerts
                         (id TEXT PRIMARY KEY, timestamp TEXT, title TEXT, 
                          severity TEXT, status TEXT, details TEXT)''')
            
            conn.commit()
            conn.close()

    def insert_event(self, event_data):
        """Insert a single event dictionary."""
        with _db_lock:
            conn = self._get_conn()
            c = conn.cursor()
            try:
                # Ensure all fields are present
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

    def get_recent_events(self, limit=100):
        """Retrieve most recent events."""
        # lock is less critical for reads, but good for safety
        with _db_lock:
            conn = self._get_conn()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = c.fetchall()
            conn.close()
            
            # Convert rows to dicts
            results = []
            for row in rows:
                d = dict(row)
                # Try to load full raw_log if possible for extra fields
                try:
                    if d.get('raw_log'):
                        full_data = json.loads(d['raw_log'])
                        d.update(full_data) # Merge full data back
                except:
                    pass
                results.append(d)
                
            # Default sort is DESC, but user might want ASC? 
            # Usually SIEM shows newest top.
            return results
            
    def get_alerts(self, limit=50):
        """Retrieve recent alerts."""
        with _db_lock:
            conn = self._get_conn()
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = c.fetchall()
            conn.close()
            return [dict(row) for row in rows]
            
    def get_stats(self):
        """Get quick counts for dashboard."""
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

    def clear_all(self):
        """Clear all data (for testing/reset)."""
        with _db_lock:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute("DELETE FROM events")
            c.execute("DELETE FROM alerts")
            conn.commit()
            conn.close()

    def get_monthly_counts(self):
        """Get event counts grouped by month for trend analysis."""
        with _db_lock:
            conn = self._get_conn()
            c = conn.cursor()
            # SQLite strftime %Y-%m
            c.execute("""
                SELECT strftime('%Y-%m', timestamp) as month, COUNT(*) as count 
                FROM events 
                GROUP BY month 
                ORDER BY month ASC 
                LIMIT 12
            """)
            rows = c.fetchall()
            conn.close()
            return [{"month": row[0], "count": row[1]} for row in rows]

    def get_threat_categories(self):
        """Get counts of high-severity event types for category chart."""
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
        """Get specialized counts for Executive KPIs (Resolved, FP, etc)."""
        with _db_lock:
            conn = self._get_conn()
            c = conn.cursor()
            
            # Count resolved alerts
            c.execute("SELECT COUNT(*) FROM alerts WHERE status IN ('Resolved', 'Contained')")
            resolved = c.fetchone()[0]
            
            # Count False Positives
            c.execute("SELECT COUNT(*) FROM events WHERE status='False Positive'")
            false_positives = c.fetchone()[0]
            
            # Count total alerts
            c.execute("SELECT COUNT(*) FROM alerts")
            total_alerts = c.fetchone()[0]
            
            conn.close()
            return {
                "resolved_alerts": resolved,
                "false_positives": false_positives,
                "total_alerts": total_alerts
            }

# Singleton instance
db = DatabaseService()
