#!/usr/bin/env python3
import requests
from playwright.sync_api import sync_playwright
from datetime import datetime

API_URL = "https://core-api.kablowebtv.com/api/channels"

def get_dynamic_token():
    with sync_playwright() as p:
        # Headless (arayüzsüz) tarayıcıyı başlat
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        captured_token = None

        # Ağ trafiğini dinle ve core-api isteğini yakala
        def handle_request(route, request):
            nonlocal captured_token
            if "core-api.kablowebtv.com" in request.url:
                headers = request.headers
                if "authorization" in headers:
                    auth = headers["authorization"]
                    if auth.startswith("Bearer "):
                        captured_token = auth.replace("Bearer ", "")
            route.continue_()

        page.route("**/*", handle_request)
        
        try:
            print("🌐 tvheryerde.com adresine bağlanılıyor...")
            page.goto("https://tvheryerde.com", timeout=60000)
            # Sayfanın yüklenmesi ve API isteklerini tetiklemesi için bekle
            page.wait_for_timeout(8000)
        except Exception as e:
            print(f"Tarayıcı yükleme hatası: {e}")
        finally:
            browser.close()
            
        return captured_token

def generate_m3u():
    try:
        print("🔍 Tarayıcı otomasyonu ile taze token alınıyor...")
        token = get_dynamic_token()
        
        if not token:
            raise ValueError("Playwright ile Bearer token yakalanamadı!")
        
        print("✅ Token başarıyla yakalandı.")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Referer": "https://tvheryerde.com",
            "Origin": "https://tvheryerde.com",
            "Authorization": f"Bearer {token}"
        }

        print("📡 Kanallar API'den çekiliyor...")
        response = requests.get(API_URL, headers=headers, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('IsSucceeded') or not data.get('Data', {}).get('AllChannels'):
            raise ValueError("API geçersiz yanıt verdi veya token reddedildi.")
        
        m3u_lines = ["#EXTM3U"]
        for channel in data['Data']['AllChannels']:
            if not channel.get('Name') or not channel.get('StreamData', {}).get('HlsStreamUrl'):
                continue
                
            group = channel.get('Categories', [{}])[0].get('Name', 'Genel')
            if group == "Bilgilendirme":
                continue
                
            m3u_lines.append(
                f'#EXTINF:-1 tvg-id="{channel.get("Id", "")}" tvg-name="{channel["Name"]}" '
                f'tvg-logo="{channel.get("PrimaryLogoImageUrl", "")}" '
                f'group-title="{group}",{channel["Name"]}\n'
                f'{channel["StreamData"]["HlsStreamUrl"]}'
            )
        
        with open("kablo_tv.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
        
        print("✅ M3U başarıyla güncellendi ve kaydedildi!")
        return True
        
    except Exception as e:
        error_msg = f"{datetime.now().isoformat()} - HATA: {str(e)}"
        print(error_msg)
        with open("error.log", "a", encoding="utf-8") as f:
            f.write(error_msg + "\n")
        return False

if __name__ == "__main__":
    generate_m3u()
