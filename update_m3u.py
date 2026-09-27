#!/usr/bin/env python3
import json
from playwright.sync_api import sync_playwright
from datetime import datetime

API_URL = "https://core-api.kablowebtv.com/api/channels"

def generate_m3u():
    try:
        print("🌐 Tarayıcı başlatılıyor ve tvheryerde.com açılıyor...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
                referer="https://tvheryerde.com"
            )
            page = context.new_page()
            
            # --- DEBUG / YAKALAMA MEKANİZMASI ---
            captured_token = None
            
            def handle_route(route, request):
                nonlocal captured_token
                # KabloTV API isteklerini yakala ve logla
                if "core-api.kablowebtv.com" in request.url:
                    headers = request.headers
                    auth_header = headers.get("authorization", "")
                    
                    print(f"\n--- [DEBUG] İstek Atılan URL: {request.url} ---")
                    print(f"--- [DEBUG] Tüm Headerlar: {json.dumps(headers, indent=2)} ---")
                    
                    if auth_header.startswith("Bearer "):
                        captured_token = auth_header.replace("Bearer ", "")
                        print(f"🎯 [DEBUG] Başarıyla Yakalanan Token:\n{captured_token}\n")
                        
                        # JWT Doğrulama (Nokta sayısından kontrol)
                        parts = captured_token.split('.')
                        if len(parts) == 3:
                            print("✅ [DEBUG] Bu geçerli bir JWT formatıdır (3 parçadan oluşuyor).")
                        else:
                            print("⚠️ [DEBUG] Uyarı: Token standart JWT yapısında görünmüyor!")
                    else:
                        print("⚠️ [DEBUG] İstekte Authorization Bearer başlığı bulunamadı!")
                        
                route.continue_()

            # Tüm ağ trafiğini yukarıdaki fonksiyonla dinle
            context.route("**/*", handle_route)
            # ------------------------------------

            # Sayfaya git ve API isteklerinin tetiklenmesini bekle
            page.goto("https://tvheryerde.com", timeout=60000)
            page.wait_for_timeout(6000)
            
            print("📡 Tarayıcı üzerinden Kanallar API'sine istek atılıyor...")
            
            # Tarayıcı içinde fetch kullanarak veriyi çek
            api_response = page.evaluate("""async (url) => {
                const res = await fetch(url, {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Origin': 'https://tvheryerde.com',
                        'Referer': 'https://tvheryerde.com'
                    }
                });
                return await res.json();
            }""", API_URL)
            
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
