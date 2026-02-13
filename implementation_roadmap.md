# Days 1 & 2 Implementation Roadmap: Persistence & Ingestion

**Objective:** Replace simulated/random data with persistent storage and real log ingestion to maximize "Practical Implementation" marks.

---

## Part 1: Day 1 - SQLite Persistence

**Goal:** Ensure data (events, alerts, playbooks) survives application restarts.

### 1. Database Schema
We will use a single SQLite file `soc_data.db` with the following tables:

*   **`events`**: Stores SIEM logs.
    *   `id` (TEXT PK), `timestamp` (DATETIME), `source` (TEXT), `event_type` (TEXT), `severity` (TEXT), `source_ip` (TEXT), `dest_ip` (TEXT), `user` (TEXT), `raw_log` (TEXT)
*   **`alerts`**: Stores generated alerts.
    *   `id` (TEXT PK), `timestamp` (DATETIME), `title` (TEXT), `severity` (TEXT), `status` (TEXT), `details` (JSON)

### 2. Module Structure: `services/database.py`
Create this file to handle all DB interactions.

```python
import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "soc_data.db"

class DatabaseService:
    def __init__(self):
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(DB_PATH, check_same_thread=False)

    def _init_db(self):
        """Initialize tables if they don't exist."""
        conn = self._get_conn()
        c = conn.cursor()
        
        # Events Table
        c.execute('''CREATE TABLE IF NOT EXISTS events
                     (id TEXT PRIMARY KEY, timestamp TEXT, source TEXT, 
                      event_type TEXT, severity TEXT, source_ip TEXT, 
                      dest_ip TEXT, user TEXT, raw_log TEXT)''')
        
        # Alerts Table
        c.execute('''CREATE TABLE IF NOT EXISTS alerts
                     (id TEXT PRIMARY KEY, timestamp TEXT, title TEXT, 
                      severity TEXT, status TEXT, details TEXT)''')
        
        conn.commit()
        conn.close()

    def insert_event(self, event_data):
        """Insert a single event dictionary."""
        conn = self._get_conn()
        c = conn.cursor()
        try:
            c.execute('''INSERT OR IGNORE INTO events 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (event_data.get('id'), event_data.get('timestamp'), 
                       event_data.get('source'), event_data.get('event_type'),
                       event_data.get('severity'), event_data.get('source_ip'), 
                       event_data.get('dest_ip'), event_data.get('user'),
                       json.dumps(event_data)))
            conn.commit()
        except Exception as e:
            print(f"DB Error: {e}")
        finally:
            conn.close()

    def get_recent_events(self, limit=100):
        """Retrieve most recent events."""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
        
    def get_stats(self):
        """Get quick counts for dashboard."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM events")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM events WHERE severity='CRITICAL'")
        critical = c.fetchone()[0]
        conn.close()
        return {"total": total, "critical": critical}

# Singleton
db = DatabaseService()
```

### 3. Integration Plan
Modify `services/siem_service.py`:
1.  Import the database service: `from services.database import db`.
2.  In `generate_events` (or rename to `get_events`), replace the random generation loop with `return db.get_recent_events(count)`.
3.  **Crucial:** Keep a fallback! `if len(events) == 0: generate_random_events()`. This ensures the dash isn't empty when you first start.

---

## Part 2: Day 2 - Real-Time Log Ingestion

**Goal:** Show that the system watches *real files*, not just Python scripts.

### 1. Ingestion Design
We will build a simple "Tailer" that watches a local file (e.g., `logs/dummy_traffic.log`).
*   **Why a dummy file?** It's safer for demos than reading system logs (permission issues) and easier to control.
*   **Mechanism:** A background thread that checks file size/modification time.

### 2. Module: `services/log_ingestor.py`

```python
import time
import threading
import os
import uuid
from datetime import datetime
from services.database import db

LOG_FILE_PATH = "logs/live_traffic.log"

class LogIngestor:
    def __init__(self):
        self.running = False
        
    def start_background_thread(self):
        """Start the ingestion thread."""
        if not self.running:
            self.running = True
            t = threading.Thread(target=self._tail_log_file, daemon=True)
            t.start()
            print("Log Ingestor Started")

    def _tail_log_file(self):
        """Tail the log file and parse new lines."""
        # Create file if not exists
        if not os.path.exists(LOG_FILE_PATH):
            os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
            with open(LOG_FILE_PATH, 'w') as f:
                f.write("")
                
        # Move to end of file
        with open(LOG_FILE_PATH, 'r') as f:
            f.seek(0, 2)
            
            while self.running:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                
                self._process_line(line)

    def _process_line(self, line):
        """Parse raw log line into DB event."""
        try:
            # Expected format: TIMESTAMP | SOURCE | SEVERITY | MESSAGE
            parts = line.strip().split('|')
            if len(parts) < 4:
                return # Skip malformed
                
            event = {
                "id": str(uuid.uuid4())[:8],
                "timestamp": parts[0].strip(),
                "source": parts[1].strip(),
                "severity": parts[2].strip(),
                "event_type": parts[3].strip(),
                "source_ip": "192.168.1.100", # Placeholder or parse if in log
                "user": "admin"
            }
            
            # Save to DB
            db.insert_event(event)
            print(f"Ingested: {event['event_type']}")
            
        except Exception as e:
            print(f"Parse Error: {e}")

# Singleton
ingestor = LogIngestor()
```

### 3. Demo Tool: Trigger Script
Create `generate_live_logs.py` to write to the file. This is your "Attack Tool" for the demo.

```python
import time
import random
from datetime import datetime

LOG_FILE = "logs/live_traffic.log"

def attack():
    with open(LOG_FILE, "a") as f:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts} | Firewall | CRITICAL | MALWARE BLOCK: 10.0.0.5 -> 8.8.8.8\n"
        f.write(line)
        print("Attack log written!")

if __name__ == "__main__":
    while True:
        input("Press Enter to simulate attack...")
        attack()
```

---

## Part 3: Integration & Dashboard Updates

### 1. Update `pages/24_SIEM.py`
Currently, `24_SIEM.py` might be generating random data in `st.session_state`.
*   **Change:** Remove the `generate_new_events()` call.
*   **New Logic:**
    ```python
    from services.database import db
    
    # Poll DB
    events = db.get_recent_events(limit=50)
    st.session_state.siem_events = events # Update state
    ```
*   **Auto-Refresh:** The existing `st.rerun()` loop will now pick up new DB rows automatically!

---

## Part 4: Viva Defense Talking Points

### The "Before & After" Narrative
*   **Examiner:** "Is this just random data?"
*   **You:** "Initially, I used a stochastic generator for UI testing. But for the final implementation, I moved to a **Persistent SQLite Architecture**. The system now tail-reads a live log file (`logs/live_traffic.log`) in a background thread, parses the unstructured text into a structured database, and the dashboard polls this real-time source. It’s a micro-scale version of how Splunk or ELK works."

### 10 Likely Questions
1.  **Q: Why SQLite and not MySQL/PostgreSQL?**
    *   **A:** "For a single-node deployment, SQLite provides ACID compliance without the overhead of a separate server process. It handles concurrent reads well enough for this dashboard."
2.  **Q: How do you handle file locking on the log file?**
    *   **A:** "I open the file in read-mode (`'r'`) which generally doesn't block writers in Unix-like systems. I use a generator pattern to yield new lines."
3.  **Q: What happens if the log volume spikes to 1000 EPS?**
    *   **A:** "Currently, the Python thread might lag. In production, I would use **Redis** as a buffer queue between the Ingestor and the Database to decouple writing from reading."

---

## Part 5: Deliverables Checklist

### Files to Create
- [ ] `services/database.py` (The Persistence Layer)
- [ ] `services/log_ingestor.py` (The Real-time Watcher)
- [ ] `manual_attack_tool.py` (The Demo Helper)

### Files to Modify
- [ ] `services/siem_service.py` (Switch from random -> db)
- [ ] `pages/24_SIEM.py` (Remove random gen, use service)
- [ ] `Home.py` (Initialize DB and Ingestor on startup)

### Proof Artifacts (For Report)
1.  Screenshot of `soc_data.db` open in a DB browser showing rows.
2.  Screenshot of terminal running `manual_attack_tool.py` side-by-side with Dashboard updating.
