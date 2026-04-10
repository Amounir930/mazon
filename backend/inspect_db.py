import sqlite3
import os
from pathlib import Path

app_data_dir = Path(os.getenv("APPDATA")) / "CrazyLister"
db_path = app_data_dir / "crazy_lister.db"

print(f"Checking DB at: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Tables: {tables}")
conn.close()
