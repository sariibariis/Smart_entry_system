import sqlite3

conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()

cursor.execute("SELECT name, timestamp, action FROM logs ORDER BY timestamp")
veriler = cursor.fetchall()

print("\n📋 Giriş / Çıkış Logları:\n")
print("{:<20} {:<20} {:<10}".format("İsim", "Zaman", "İşlem"))
print("-" * 50)

for name, timestamp, action in veriler:
    print("{:<20} {:<20} {:<10}".format(name, timestamp, action))

conn.close()

