import cv2
import dlib
import pickle
import os
import sqlite3
from datetime import datetime
import numpy as np
from scipy.spatial import distance as dist

# Dlib model dosyaları
predictor_path = "shape_predictor_68_face_landmarks.dat"
face_rec_model_path = "dlib_face_recognition_resnet_model_v1.dat"
ENCODING_FILE = "encodings.pkl"
DB_FILE = "attendance.db"

# EAR (Eye Aspect Ratio) hesaplama
def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

EYE_AR_THRESH = 0.2           # Göz kapalı eşiği
BLINK_FRAMES_REQUIRED = 3     # Gerçek kırpma için gereken kapalı kare sayısı

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

# Göz landmark indexleri
LEFT_EYE_POINTS = list(range(36, 42))
RIGHT_EYE_POINTS = list(range(42, 48))

# Kamera başlat
video_capture = cv2.VideoCapture(0)
print("🎥 Tanıma sistemi çalışıyor. Gerçek göz kırpma olmadan log yapılmaz. ESC ile çık.\n")

# Göz kırpma durumu tutucu
blink_status = {}
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

        landmarks = np.array([[shape.part(i).x, shape.part(i).y] for i in range(68)])
        leftEye = landmarks[LEFT_EYE_POINTS]
        rightEye = landmarks[RIGHT_EYE_POINTS]

        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        ear = (leftEAR + rightEAR) / 2.0

        matched_name = compare_faces(data, face_encoding)

        if matched_name:
            # Her zaman yeşil çerçeve çiz ve isim yaz
            cv2.rectangle(frame, (face.left(), face.top()), (face.right(), face.bottom()), (0, 255, 0), 2)
            cv2.putText(frame, matched_name, (face.left(), face.top() - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            if matched_name not in blink_status:
                blink_status[matched_name] = 0

            # Göz kapalıysa sayacı artır
            if ear < EYE_AR_THRESH:
                blink_status[matched_name] += 1
            else:
                # Yeterince kapalı kaldıysa → logla
                if blink_status[matched_name] >= BLINK_FRAMES_REQUIRED and matched_name not in taninanlar:
                    action = determine_action(matched_name)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    cursor.execute('''
                        INSERT INTO logs (name, timestamp, action) VALUES (?, ?, ?)
                    ''', (matched_name, timestamp, action))
                    conn.commit()

                    print(f"✅ {matched_name} için {action} kaydedildi: {timestamp}")
                    taninanlar.add(matched_name)

                blink_status[matched_name] = 0

        else:
            # Tanınmayan kişi → kırmızı çerçeve
            cv2.rectangle(frame, (face.left(), face.top()), (face.right(), face.bottom()), (0, 0, 255), 2)
            cv2.putText(frame, "Bilinmeyen", (face.left(), face.top() - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            print("\033[91m❌ Tanınmayan kişi!\033[0m")

    cv2.imshow("Turnike Sistemi", frame)
    if cv2.waitKey(10) == 27:  # ESC
        print("⛔️ Sistem kapatıldı.")
        break

video_capture.release()
cv2.destroyAllWindows()
conn.close()

