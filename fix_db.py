import sqlite3
import os

db_path = 'backend/amazon.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for col in [('parent_asin', 'VARCHAR(20)'), ('variation_theme', 'VARCHAR(100)')]:
    try:
        cursor.execute(f"ALTER TABLE products ADD COLUMN {col[0]} {col[1]}")
        print(f"Added {col[0]}")
    except Exception as e:
        print(f"Skip {col[0]}: {e}")

conn.commit()
conn.close()
print("Done")
