import sqlite3

conn = sqlite3.connect("database.db")

email = "baidayhalder7@gmail.com"

conn.execute("""
    UPDATE users
    SET role = 'admin'
    WHERE email = ?
""", (email,))

conn.commit()
conn.close()

print("Admin role updated successfully!")