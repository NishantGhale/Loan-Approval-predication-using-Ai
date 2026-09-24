import sqlite3
conn = sqlite3.connect('analytics.db')
c = conn.cursor()
try:
    c.execute("SELECT * FROM requests")
    rows = c.fetchall()
    print(f"Found {len(rows)} requests.")
    for row in rows:
        print(row)
except Exception as e:
    print(f"Error: {e}")
conn.close()
