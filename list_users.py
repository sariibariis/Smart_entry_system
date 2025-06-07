import pickle
import os

ENCODING_FILE = "encodings.pkl"

if not os.path.exists(ENCODING_FILE):
    print("❌ Henüz hiç yüz kaydedilmemiş.")
    exit()

with open(ENCODING_FILE, "rb") as f:
    data = pickle.load(f)

print("📋 Kayıtlı çalışanlar:")
for i, person in enumerate(data, 1):
    print(f"{i}. {person['name']} ({len(person['encodings'])} yüz verisi)")

