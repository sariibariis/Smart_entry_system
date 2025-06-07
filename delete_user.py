import pickle
import os

ENCODING_FILE = "encodings.pkl"

if not os.path.exists(ENCODING_FILE):
    print("❌ Kayıt dosyası bulunamadı.")
    exit()

isim = input("Silmek istediğiniz çalışanın adını girin: ").strip().lower()

with open(ENCODING_FILE, "rb") as f:
    data = pickle.load(f)

# İsim eşleşmelerine göre filtrele
yeni_data = [entry for entry in data if entry["name"].lower() != isim]

if len(yeni_data) == len(data):
    print(f"❌ '{isim}' adlı kişi bulunamadı.")
else:
    with open(ENCODING_FILE, "wb") as f:
        pickle.dump(yeni_data, f)
    print(f"🗑️ '{isim}' başarıyla silindi.")

