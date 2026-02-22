from services.database import db
import pandas as pd

events = db.get_recent_events(limit=5000)
df = pd.DataFrame(events)
print(f"Total events retrieved: {len(df)}")
if not df.empty:
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    print(f"Min timestamp: {df['timestamp'].min()}")
    print(f"Max timestamp: {df['timestamp'].max()}")
    print("Date counts:")
    print(df.groupby(df['timestamp'].dt.date).size().tail(10))
