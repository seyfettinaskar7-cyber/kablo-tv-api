#!/usr/bin/env python3
import json
import time
from playwright.sync_api import sync_playwright
from datetime import datetime

API_URL = "https://core-api.kablowebtv.com/api/channels"

def generate_m3u():
    try:
        print("🌐 Tarayıcı başlatılıyor ve tvheryerde.com açılıyor...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Referer": "https://tvheryerde.com",
                    "Origin": "https://tvheryerde.com"
                }
            )
            page = context.new_page()
            
            captured_token = None
            
            # Ağ trafiğini dinleyip token'ı yakalayan fonksiyon
            def handle_route(route, request):
                nonlocal captured_token
                if "core-api.kablowebtv.com" in request.url:
                    auth_header = request.headers.get("authorization", "")
                    if auth_header.startswith("Bearer "):
                        token_val = auth_header.replace("Bearer ", "")
                        if not captured_token: # İlk yakalananı al
                            captured_token = token_val
                            print(f"🎯 [DEBUG] Ağ trafiğinden taze JWT Token yakalandı!")
                route.continue_()

            context.route("**/*", handle_route)

            # Sayfaya git
            page.goto("https://tvheryerde.com", timeout=60000)
            
            # Token'ın ağ trafiğinde belirmesi için birkaç saniye bekle
            print("⏳ Token'ın ağ trafiğinde oluşması bekleniyor...")
            start_time = time.time()
            while not captured_token and time.time() - start_time < 15:
                page.wait_for_timeout(500)
            
            if not captured_token:
                raise ValueError("Ağ trafiğinden Bearer token yakalanamadı!")
            
            print(f"✅ Yakalanan Token ile Kanallar API'sine istek atılıyor...")
            
            # Yakalanan gerçek token'ı fetch isteğinin içine Authorization olarak ekliyoruz
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
            }""", {"url": API_URL, "token": captured_token})
            
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
