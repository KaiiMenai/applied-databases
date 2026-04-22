import sqlite3
conn = sqlite3.connect('appdbproj.db')
cursor = conn.cursor()
cursor.execute("SELECT speakerName, sessionTitle FROM session WHERE speakerName LIKE '%Niamh%'")
print(cursor.fetchall())
conn.close()