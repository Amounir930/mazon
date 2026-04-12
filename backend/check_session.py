import sqlite3, json
db = r'C:\Users\Dell\AppData\Roaming\CrazyLister\crazy_lister.db'
conn = sqlite3.connect(db)
cursor = conn.cursor()

cursor.execute('SELECT id, email, auth_method, seller_name, country_code, is_active, is_valid FROM sessions WHERE is_active=1 AND is_valid=1')
rows = cursor.fetchall()
print(f'Active sessions: {len(rows)}')
for r in rows:
    print(f'  ID={r[0][:8]}..., email={r[1]}, method={r[2]}, seller={r[3]}, country={r[4]}')

if rows:
    sid = rows[0][0]
    cursor.execute('SELECT cookies_json FROM sessions WHERE id=?', (sid,))
    row = cursor.fetchone()
    if row and row[0]:
        from app.services.session_store import decrypt_data
        decrypted = decrypt_data(row[0])
        cookies = json.loads(decrypted)
        print(f'\nCookies ({len(cookies)}):')
        names = [c.get('name', '?') for c in cookies]
        print(f'  Names: {names}')
        
        # Check for key cookies
        session_id = [c for c in cookies if 'session-id' in c.get('name', '').lower()]
        at_main = [c for c in cookies if c.get('name', '') == 'at-main']
        ubid = [c for c in cookies if 'ubid' in c.get('name', '').lower()]
        
        print(f'\n  session-id cookies: {len(session_id)}')
        print(f'  at-main cookies: {len(at_main)}')
        print(f'  ubid cookies: {len(ubid)}')

conn.close()
print('\nDone!')
