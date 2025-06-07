from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import subprocess
import os
import pickle
import sqlite3
import sys
import csv
from io import StringIO, BytesIO
from datetime import datetime  # ✅ Aktif çalışan kontrolü için gerekli

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Flash mesajlar için

ENCODING_FILE = "encodings.pkl"

# Ana sayfa
@app.route('/')
def index():
    return render_template('index.html')

# Giriş/çıkış loglarını görüntüle
@app.route('/logs')
def view_logs():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY timestamp DESC")
    logs = cursor.fetchall()
    conn.close()
    return render_template('logs.html', logs=logs)



# Turnike sistemini başlat
@app.route('/start_turnike')
def start_turnike():
    subprocess.Popen(['python3', 'tanima_ve_giris_EAR.py'])
    flash("Turnike sistemi başlatıldı!", "success")
    return redirect(url_for('index'))

# Çalışanlar sayfası
@app.route('/calisanlar')
def calisanlar():
    if not os.path.exists(ENCODING_FILE):
        return render_template('calisanlar.html', employees=[])
    with open(ENCODING_FILE, "rb") as f:
        data = pickle.load(f)
    names = sorted(set(entry["name"] for entry in data))
    return render_template('calisanlar.html', employees=names)

# Yeni çalışan ekle (form)
@app.route('/ekle_calisan', methods=['GET', 'POST'])
def ekle_calisan():
    if request.method == 'POST':
        isim = request.form.get('isim').strip().lower()
        if not isim:
            flash("Isim bos birakilamaz.", "danger")
            return redirect(url_for('ekle_calisan'))

        # Zaten kayıtlı mı kontrol et
        if os.path.exists(ENCODING_FILE):
            with open(ENCODING_FILE, "rb") as f:
                data = pickle.load(f)
            for person in data:
                if person["name"] == isim:
                    flash(f"'{isim}' zaten bu isimle kayitli.", "danger")
                    return redirect(url_for('ekle_calisan'))

        # Kamera ile kayıt scriptini başlat
        result = subprocess.run(['python3', 'kayit_dupcntrl.py', isim], capture_output=True, text=True)
        stdout = result.stdout.strip().lower()

        if "bu yuz zaten" in stdout:
            flash("Bu yüz zaten farklı bir isimle sistemde kayıtlı.", "danger")
            return redirect(url_for('ekle_calisan'))

        elif "kayıt iptal edildi" in stdout or "kayit iptal edildi" in stdout:
            flash("Kayıt işlemi iptal edildi. Yüz zaten kayıtlı olabilir.", "danger")
            return redirect(url_for('ekle_calisan'))

        elif "hiç yüz kaydedilmedi" in stdout:
            flash("Yüz verisi alınamadı. Lütfen tekrar deneyin.", "danger")
            return redirect(url_for('ekle_calisan'))

        flash(f"{isim} sisteme eklendi.", "success")
        return redirect(url_for('calisanlar'))

    return render_template('ekle_calisan.html')

# Çalisan sil
@app.route('/sil/<isim>')
def sil(isim):
    with open(ENCODING_FILE, "rb") as f:
        data = pickle.load(f)
    yeni_data = [entry for entry in data if entry["name"].lower() != isim.lower()]
    with open(ENCODING_FILE, "wb") as f:
        pickle.dump(yeni_data, f)
    flash(f"{isim} silindi.", "info")
    return redirect(url_for('calisanlar'))

# Loglari temizle
@app.route('/clear_logs')
def clear_logs():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM logs")
    conn.commit()
    conn.close()
    flash("Tum loglar temizlendi.", "info")
    return redirect(url_for('view_logs'))

# Loglari CSV olarak dışa aktar
@app.route('/export_logs')
def export_logs():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY timestamp DESC")
    logs = cursor.fetchall()
    conn.close()

    output_str = StringIO()
    writer = csv.writer(output_str)
    writer.writerow(['ID', 'Isim', 'Zaman', 'Islem'])
    writer.writerows(logs)
    output_bytes = BytesIO(output_str.getvalue().encode('utf-8'))

    return send_file(
        output_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name='giris_cikis_loglari.csv'
    )

# ✅ YENİ ROUTE: Aktif çalışanları listele
@app.route('/aktif_calisanlar')
def aktif_calisanlar():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    # En son giriş/çıkış zamanlarını çek
    cursor.execute("""
        SELECT name, MAX(timestamp)
        FROM logs
        GROUP BY name
    """)
    last_entries = cursor.fetchall()

    aktifler = []

    # Her çalışanın son işlemine bak → "giriş" ise içeride
    for name, timestamp in last_entries:
        cursor.execute("SELECT action FROM logs WHERE name = ? AND timestamp = ?", (name, timestamp))
        action = cursor.fetchone()
        if action and action[0].lower() == "giriş":
            aktifler.append((name, timestamp))

    conn.close()
    return render_template("aktif_calisanlar.html", aktifler=aktifler)
from datetime import datetime

@app.route('/calisma_sureleri', methods=['GET', 'POST'])
def calisma_sureleri():
    tarih = request.form.get('tarih') if request.method == 'POST' else None
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    if tarih:
        # Belirli bir günün verilerini çek
        cursor.execute("SELECT name, timestamp, action FROM logs WHERE DATE(timestamp) = ? ORDER BY name, timestamp", (tarih,))
    else:
        # Tüm loglardan hesapla
        cursor.execute("SELECT name, timestamp, action FROM logs ORDER BY name, timestamp")

    logs = cursor.fetchall()
    conn.close()

    # Hesaplama
    calisma_sureleri = {}
    giris_zamani = {}

    for name, timestamp, action in logs:
        timestamp_dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

        if action.lower() == "giriş":
            giris_zamani[name] = timestamp_dt
        elif action.lower() == "çıkış" and name in giris_zamani:
            sure = timestamp_dt - giris_zamani[name]
            if name in calisma_sureleri:
                calisma_sureleri[name] += sure
            else:
                calisma_sureleri[name] = sure
            del giris_zamani[name]

    return render_template("calisma_sureleri.html", calisma_sureleri=calisma_sureleri, tarih=tarih)


# Uygulama çalıştırma
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
