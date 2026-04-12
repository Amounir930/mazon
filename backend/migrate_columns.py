"""Add missing columns to products table"""
import sqlite3

DB_PATH = r"C:\Users\Dell\AppData\Roaming\CrazyLister\crazy_lister.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Get existing columns
c.execute("PRAGMA table_info(products)")
existing = [row[1] for row in c.fetchall()]
print(f"Existing columns: {len(existing)}")

new_cols = [
    ("material", "VARCHAR(200)", "''"),
    ("number_of_items", "INTEGER", "1"),
    ("unit_count", "TEXT", "NULL"),
    ("target_audience", "VARCHAR(100)", "''"),
]

for name, dtype, default in new_cols:
    if name in existing:
        print(f"  ✅ {name} (exists)")
    else:
        try:
            c.execute(f"ALTER TABLE products ADD COLUMN {name} {dtype} DEFAULT {default}")
            print(f"  ✅ {name} (added)")
        except Exception as e:
            print(f"  ❌ {name}: {e}")

conn.commit()

# Verify
c.execute("PRAGMA table_info(products)")
final = [row[1] for row in c.fetchall()]
print(f"\nFinal columns: {len(final)}")
for name, _, _ in new_cols:
    print(f"  {'✅' if name in final else '❌'} {name}")

conn.close()
print("\n✅ Migration complete")
