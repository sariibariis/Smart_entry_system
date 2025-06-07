import os

def main_menu():
    while True:
        print("\n📋 SMART ENTRY SYSTEM")
        print("1. Yeni çalışan kaydı yap")
        print("2. Kayıtlı çalışanları listele")
        print("3. Çalışan sil")
        print("4. Turnike sistemini başlat (tanıma + giriş/çıkış)")
        print("5. Giriş/çıkış loglarını listele")
        print("6. Tüm log kayıtlarını temizle")
        print("0. Çıkış")

        secim = input("\nBir seçenek girin: ").strip()

        if secim == "1":
            os.system("python3 kayit_dupcntrl.py")  # ← burada düzeltme yaptık
        elif secim == "2":
            os.system("python3 list_users.py")
        elif secim == "3":
            os.system("python3 delete_user.py")
        elif secim == "4":
            os.system("python3 tanima_ve_giris.py")
        elif secim == "5":
            os.system("python3 listele_kayitlar.py")
        elif secim == "6":
            os.system("python3 clear_logs.py")
        elif secim == "0":
            print("👋 Çıkılıyor...")
            break
        else:
            print("❌ Geçersiz seçim. Tekrar deneyin.")

if __name__ == "__main__":
    main_menu()




       
