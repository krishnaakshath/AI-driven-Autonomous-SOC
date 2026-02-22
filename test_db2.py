from services.database import db
import pandas as pd

events = db.get_all_events()
df = pd.DataFrame(events)
print(f"Total events in DB: {len(df)}")
if not df.empty:
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    print(f"Min timestamp: {df['timestamp'].min()}")
    print(f"Max timestamp: {df['timestamp'].max()}")
    print("Monthly counts:")
    df['month'] = df['timestamp'].dt.to_period('M')
    print(df.groupby('month').size())
