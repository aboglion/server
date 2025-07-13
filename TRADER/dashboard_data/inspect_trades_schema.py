import sqlite3

conn = sqlite3.connect("dashboard_data/DashboardData.db")
c = conn.cursor()
c.execute("PRAGMA table_info(trades)")
columns = c.fetchall()
for col in columns:
    print(col)
conn.close()