#!/usr/bin/env python3
import json
from playwright.sync_api import sync_playwright
from datetime import datetime

API_CHANNELS_URL = "core-api.kablowebtv.com/api/channels"

def generate_m3u():
    try:
        print("🌐 Tarayıcı başlatılıyor ve tvheryerde.com açılıyor...")
        captured_api_data = None
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
                extra_http_headers={
                    "Referer": "https://tvheryerde.com",
                    "Origin": "https://tvheryerde.com"
                }
            )
            page = context.new_page()
            
            # 1. İstekleri dinleyip Token'ı Debug'a yazdıralım
            def handle_request(request):
                if "core-api.kablowebtv.com" in request.url:
                    auth_header = request.headers.get("authorization", "")
                    if auth_header.startswith("Bearer "):
                        token = auth_header.replace("Bearer ", "")
                        print(f"\n🔑 [DEBUG] Yakalanan JWT Token:\n{token}\n")

            page.on("request", handle_request)

            # 2. Kanallar API'sinin verdiği yanıtı (response) doğrudan yakalayalım
            def handle_response(response):
                nonlocal captured_api_data
                if API_CHANNELS_URL in response.url and response.status == 200:
                    try:
                        json_data = response.json()
                        if json_data.get('IsSucceeded'):
                            captured_api_data = json_data
                            print("🎯 [DEBUG] Kanallar API'sinin başarılı yanıtı doğrudan ağ trafiğinden yakalandı!")
                    except Exception:
                        pass

            page.on("response", handle_response)

            # Sayfaya git
            page.goto("https://tvheryerde.com", timeout=60000)
            
            # Ağ trafiğinden verinin gelmesi için biraz bekle
            print("⏳ Sayfanın yüklenmesi ve kanal verilerinin gelmesi bekleniyor...")
            page.wait_for_timeout(8000)
            
            browser.close()
            
        if not captured_api_data or not captured_api_data.get('Data', {}).get('AllChannels'):
            raise ValueError("API verisi ağ trafiğinden yakalanamadı!")
        
        data = captured_api_data
        print("✅ Kanallar işleniyor, M3U oluşturuluyor...")
        
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
