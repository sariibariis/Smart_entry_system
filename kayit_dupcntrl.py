import sys
import cv2
import dlib
import pickle
import os
import time
import numpy as np
from scipy.spatial import distance

# Gerekli dosya yolları
predictor_path = "shape_predictor_68_face_landmarks.dat"
face_rec_model_path = "dlib_face_recognition_resnet_model_v1.dat"
ENCODING_FILE = "encodings.pkl"

# Dlib modellerini yükle
detector = dlib.get_frontal_face_detector()
sp = dlib.shape_predictor(predictor_path)
face_rec_model = dlib.face_recognition_model_v1(face_rec_model_path)

# Kullanıcıdan isim al
if len(sys.argv) > 1:
    isim = sys.argv[1].strip().lower()
else:
    isim = input("Çalışan ismini girin: ").strip().lower()







# Mevcut verileri yükle
if os.path.exists(ENCODING_FILE):
    with open(ENCODING_FILE, "rb") as f:
        data = pickle.load(f)
else:
    data = []

# Aynı isimle kayıt varsa uyar ve çık
for person in data:
    if person["name"] == isim:
        print(f"⚠️ '{isim}' zaten kayıtlı. Lütfen farklı bir isim girin veya eski kaydı silin.")
        exit()

# Kamera başlat
video_capture = cv2.VideoCapture(0)
print("\n📸 Kameraya bakın. Sistem otomatik olarak 10 yüz örneği toplayacak...\n")

encodings = []
toplanacak_yuz_sayisi = 10
sure_arasi = 1.5
son_kayit_zamani = time.time()

def is_same_face(new_encoding, existing_data, tolerance=0.5):
    for person in existing_data:
        for enc in person["encodings"]:
            dist = distance.euclidean(enc, new_encoding)
            if dist < tolerance:
                return person["name"]
    return None

while len(encodings) < toplanacak_yuz_sayisi:
    ret, frame = video_capture.read()
    if not ret:
        print("Kamera görüntüsü alınamadı.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    faces = detector(gray)

    for face in faces:
        cv2.rectangle(frame, (face.left(), face.top()), (face.right(), face.bottom()), (0, 255, 0), 2)

        if (time.time() - son_kayit_zamani) > sure_arasi:
            shape = sp(rgb, face)
            face_descriptor = face_rec_model.compute_face_descriptor(rgb, shape)
            enc_np = np.array(face_descriptor)

            # Aynı yüz daha önce kayıtlı mı kontrol et
            matched_name = is_same_face(enc_np, data)
            if matched_name:
                print(f"❌ Bu yüz zaten '{matched_name}' adıyla kayıtlı. Kayıt iptal edildi.")
                video_capture.release()
                cv2.destroyAllWindows()
                exit()

            encodings.append(enc_np)
            son_kayit_zamani = time.time()
            print(f"✅ {len(encodings)}/{toplanacak_yuz_sayisi} yüz kaydedildi.")

    cv2.imshow("Kamera - Yüz Kaydı (ESC ile çık)", frame)
    if cv2.waitKey(10) == 27:  # ESC ile çık
        print("⛔️ Kayıt erken sonlandırıldı.")
        break

video_capture.release()
cv2.destroyAllWindows()

if not encodings:
    print("❌ Hiç yüz kaydedilmedi.")
    exit()

# Yeni kullanıcıyı veriye ekle
data.append({
    "name": isim,
    "encodings": encodings
})

with open(ENCODING_FILE, "wb") as f:
    pickle.dump(data, f)

print(f"\n✅ {isim} başarıyla {len(encodings)} yüz verisiyle sisteme kaydedildi.")

