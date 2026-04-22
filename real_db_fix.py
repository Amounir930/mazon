import sqlite3
import os
from pathlib import Path

# Windows AppData path as defined in database.py
app_data_dir = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CrazyLister"
db_path = app_data_dir / "crazy_lister.db"

print(f"Targeting database: {db_path}")

if not db_path.exists():
    print("❌ Database file not found!")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Diagnostic
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(f"Tables found: {[t[0] for t in cursor.fetchall()]}")

# Migration
for col in [('parent_asin', 'VARCHAR(20)'), ('variation_theme', 'VARCHAR(100)')]:
    try:
        cursor.execute(f"ALTER TABLE products ADD COLUMN {col[0]} {col[1]}")
        print(f"✅ Added {col[0]}")
    except Exception as e:
        print(f"❌ {col[0]}: {e}")

conn.commit()
conn.close()
print("🚀 Manual migration complete!")
