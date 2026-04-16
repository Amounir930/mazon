import sqlite3
conn = sqlite3.connect(r'C:\Users\Dell\AppData\Roaming\CrazyLister\crazy_lister.db')
c = conn.cursor()
c.execute("SELECT unit_count FROM products ORDER BY rowid DESC LIMIT 5")
for row in c.fetchall():
    print(row[0])
