#!/usr/bin/env python3
import json
import time
from playwright.sync_api import sync_playwright
from datetime import datetime

API_CHANNELS_URL = "https://core-api.kablowebtv.com/api/channels"

def generate_m3u():
    try:
        print("🌐 Tarayıcı başlatılıyor ve tvheryerde.com açılıyor...")
        captured_token = None
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Referer": "https://tvheryerde.com",
                    "Origin": "https://tvheryerde.com"
                }
            )
            page = context.new_page()
            
            # 1. Ağ trafiğinden taze token'ı yakala
            def handle_request(request):
                nonlocal captured_token
                if "core-api.kablowebtv.com" in request.url:
                    auth_header = request.headers.get("authorization", "")
                    if auth_header.startswith("Bearer "):
                        token = auth_header.replace("Bearer ", "")
                        if not captured_token:
                            captured_token = token
                            print(f"🔑 [DEBUG] Yakalanan Taze JWT Token: {token[:30]}...")

            page.on("request", handle_request)

            # Sayfaya git
            print("🌐 Sayfa yükleniyor...")
            page.goto("https://tvheryerde.com", timeout=60000)
            
            # Token'ın ağ trafiğinde oluşması için max 15 saniye bekle
            start_time = time.time()
            while not captured_token and time.time() - start_time < 15:
                page.wait_for_timeout(500)
                
            if not captured_token:
                raise ValueError("Ağ trafiğinden JWT token yakalanamadı!")
            
            print("📡 Yakalanan taze token ile tarayıcı içinde Channels API'sine istek atılıyor...")
            
            # 2. Yakaladığımız taze token'ı kullanarak tarayıcı içinde doğrudan fetch at
            api_response = page.evaluate("""async ({ url, token }) => {
                const res = await fetch(url, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Authorization': 'Bearer ' + token,
                        'Origin': 'https://tvheryerde.com',
                        'Referer': 'https://tvheryerde.com'
                    }
                });
                return await res.json();
            }""", {"url": API_CHANNELS_URL, "token": captured_token})
            
            browser.close()
            
        data = api_response
        
        if not data or not data.get('IsSucceeded') or not data.get('Data', {}).get('AllChannels'):
            raise ValueError(f"API'den geçerli veri alınamadı. Yanıt: {str(data)[:150]}")
        
        print("✅ Kanallar başarıyla alındı, M3U oluşturuluyor...")
        
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
