import sqlite3

conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM logs")
conn.commit()
conn.close()

print("🧹 Tüm giriş/çıkış logları başarıyla silindi.")

