import re
import requests

# Hedef URL (örnek olarak tvheryerde.com veya istek attığın uç nokta)
url = "https://tvheryerde.com"

try:
  # Sayfanın kaynak kodunu veya ilgili API yanıtını çekiyoruz
  headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  }
  response = requests.get(url, headers=headers)

  # JWT formatına uygun metinleri aramak için regex deseni
  jwt_pattern = r"eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+"

  # Eşleşmeleri bul
  matches = re.findall(jwt_pattern, response.text)

  if matches:
    print(f"[+] Toplam {len(matches)} adet token bulundu:")

    # Token'ları bearer.txt dosyasına kaydetme
    with open("bearer.txt", "w", encoding="utf-8") as f:
      for i, token in enumerate(matches, 1):
        print(f"{i}. Token: {token}")
        f.write(token + "\n")  # Her token'ı yeni bir satıra yazar

    print("[+] Tüm token'lar 'bearer.txt' dosyasına başarıyla kaydedildi!")
  else:
    print(
        "[-] Sayfada eşleşen bir token bulunamadı. (Site dinamik JS ile"
        " yüklüyor olabilir)"
    )

except Exception as e:
  print(f"[!] Bir hata oluştu: {e}")
