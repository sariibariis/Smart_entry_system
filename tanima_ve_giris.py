import cv2
import dlib
import pickle
import os
import sqlite3
from datetime import datetime
import numpy as np

# Dlib model dosyaları
predictor_path = "shape_predictor_68_face_landmarks.dat"
face_rec_model_path = "dlib_face_recognition_resnet_model_v1.dat"
ENCODING_FILE = "encodings.pkl"
DB_FILE = "attendance.db"

# Dlib modelleri
detector = dlib.get_frontal_face_detector()
sp = dlib.shape_predictor(predictor_path)
face_rec_model = dlib.face_recognition_model_v1(face_rec_model_path)

# Encoding verisini yükle
if not os.path.exists(ENCODING_FILE):
    print("❌ Kayıtlı yüz verisi bulunamadı.")
    exit()

with open(ENCODING_FILE, "rb") as f:
    data = pickle.load(f)

# Veritabanı bağlantısı ve tablo oluşturma
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        action TEXT NOT NULL
    )
''')
conn.commit()

# Giriş/çıkış kontrol fonksiyonu
def determine_action(name):
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('''
        SELECT action FROM logs
        WHERE name = ? AND DATE(timestamp) = ?
        ORDER BY id DESC LIMIT 1
    ''', (name, today))
    result = cursor.fetchone()

    if result is None:
        return "Giriş"
    elif result[0] == "Giriş":
        return "Çıkış"
    else:
        return "Giriş"

# Yüz karşılaştırma fonksiyonu
def compare_faces(known_encodings, face_encoding, tolerance=0.5):
    for person in known_encodings:
        for enc in person["encodings"]:
            dist = np.linalg.norm(enc - face_encoding)
            if dist < tolerance:
                return person["name"]
    return None

# Kamera başlat
video_capture = cv2.VideoCapture(0)
print("🎥 Tanıma sistemi çalışıyor. ESC ile çıkabilirsiniz.\n")

taninanlar = set()

while True:
    ret, frame = video_capture.read()
    if not ret:
        print("Kamera alınamadı.")
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    for face in faces:
        shape = sp(rgb, face)
        face_descriptor = face_rec_model.compute_face_descriptor(rgb, shape)
        face_encoding = np.array(face_descriptor)

        matched_name = compare_faces(data, face_encoding)

        if matched_name and matched_name not in taninanlar:
            # Yeni tanınan kişi için logla
            action = determine_action(matched_name)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute('''
                INSERT INTO logs (name, timestamp, action) VALUES (?, ?, ?)
            ''', (matched_name, timestamp, action))
            conn.commit()

            print(f"✅ {matched_name} için {action} kaydedildi: {timestamp}")
            taninanlar.add(matched_name)

            # Çerçeve çiz ve isim yaz (YEŞİL)
            cv2.rectangle(frame, (face.left(), face.top()), (face.right(), face.bottom()), (0, 255, 0), 2)
            cv2.putText(frame, matched_name, (face.left(), face.top() - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        elif matched_name is None:
            # Tanınmayan yüz için KIRMIZI çerçeve ve uyarı
            cv2.rectangle(frame, (face.left(), face.top()), (face.right(), face.bottom()), (0, 0, 255), 2)
            cv2.putText(frame, "Bilinmeyen", (face.left(), face.top() - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            print("\033[91m❌ Tanınmayan kişi!\033[0m")  # Kırmızı terminal uyarısı

    cv2.imshow("Turnike Sistemi", frame)
    if cv2.waitKey(10) == 27:  # ESC ile çık
        print("⛔️ Sistem kapatıldı.")
        break

video_capture.release()
cv2.destroyAllWindows()
conn.close()

