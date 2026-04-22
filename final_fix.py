import sqlite3
db_path = r'C:\Users\Dell\Desktop\learn\amazon\backend\amazon.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(f"Tables: {cursor.fetchall()}")

# Try migration here too
for col in [('parent_asin', 'VARCHAR(20)'), ('variation_theme', 'VARCHAR(100)')]:
    try:
        cursor.execute(f"ALTER TABLE products ADD COLUMN {col[0]} {col[1]}")
        print(f"✅ Added {col[0]}")
    except Exception as e:
        print(f"❌ {col[0]}: {e}")

conn.commit()
conn.close()
