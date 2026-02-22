from services.database import db
import pandas as pd

events = db.get_recent_events(limit=5000)
print("Len of get_recent_events(5000):", len(events))
