import re
import sys

def strip_sqlite_from_database(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # 1. Remove imports
    content = re.sub(r'import sqlite3\n', '', content)
    content = re.sub(r'import threading\n', '', content)

    # 2. Remove locks
    content = re.sub(r'_db_lock = threading.Lock\(\)\n', '', content)
    content = re.sub(r'DB_PATH = "soc_data.db"\n', '', content)

    # 3. Modify class init
    init_func = r'''    def __init__\(self\):
        self._supabase = None
        self._use_supabase = False
        
        # Try Supabase first
        if SUPABASE_URL and SUPABASE_KEY:
            self._supabase = SupabaseClient\(SUPABASE_URL, SUPABASE_KEY\)
            try:
                self._use_supabase = self._supabase.is_connected\(\)
            except Exception:
                self._use_supabase = False
        
        if not self._use_supabase:
            print\("\[DB\] Using SQLite fallback \(local mode\)"\)
        
        # Always init SQLite as fallback
        self._init_sqlite\(\)'''

    new_init_func = '''    def __init__(self):
        self._supabase = None
        self._use_supabase = False
        
        if SUPABASE_URL and SUPABASE_KEY:
            self._supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
            try:
                self._use_supabase = self._supabase.is_connected()
            except Exception:
                self._use_supabase = False
        
        if not self._use_supabase:
            print("[DB] CRITICAL WARNING: Supabase is unreachable. System may fail.")'''

    content = re.sub(init_func, new_init_func, content)

    print("File modified.")
    with open('services/database_clean.py', 'w') as f:
        f.write(content)

if __name__ == "__main__":
    strip_sqlite_from_database("services/database.py")
