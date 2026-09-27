#!/usr/bin/env python3
import json
import time
from playwright.sync_api import sync_playwright
from datetime import datetime

API_CHANNELS_URL = "https://core-api.kablowebtv.com/api/channels"

def generate_m3u():
    try:
        print("📟 iPad (Tablet) profili başlatılıyor (Uygulama yönlendirmesini aşmak için)...")
        captured_data = None
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu'
                ]
            )
            
            # iPad (Tablet) profili taklit ediyoruz
            context = browser.new_context(
                user_agent="Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                viewport={"width": 1024, "height": 768},
                device_scale_factor=2,
                is_mobile=True,
                has_touch=True,
                locale="tr-TR",
                timezone_id="Europe/Istanbul",
                extra_http_headers={
                    "Referer": "https://tvheryerde.com/",
                    "Origin": "https://tvheryerde.com",
                    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
                }
            )
            
            # Stealth enjeksiyonu
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.navigator.chrome = {
                    runtime: {}
                };
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['tr-TR', 'tr', 'en-US', 'en']
                });
            """)
            
            page = context.new_page()
            
            # Ağ trafiğindeki /api/channels yanıtını dinle
            def handle_response(response):
                nonlocal captured_data
                if "/api/channels" in response.url:
                    try:
                        json_data = response.json()
                        if json_data.get('IsSucceeded'):
                            captured_data = json_data
                            print("🎯 [DEBUG] iPad modunda Channels API yanıtı başarıyla yakalandı!")
                    except Exception:
                        pass

            page.on("response", handle_response)

            print("🌐 tvheryerde.com iPad tarayıcı modunda açılıyor...")
            page.goto("https://tvheryerde.com", timeout=60000)
            
            # Sayfanın yüklenmesi ve API isteğini tetiklemesi için bekle
            start_time = time.time()
            while not captured_data and time.time() - start_time < 20:
                page.wait_for_timeout(1000)
                if not captured_data and time.time() - start_time > 6:
                    try:
                        page.mouse.wheel(0, 300)
                    except Exception:
                        pass

            browser.close()
            
        if not captured_data or not captured_data.get('Data', {}).get('AllChannels'):
            raise ValueError("iPad modunda da API yanıtı alınamadı.")
        
        data = captured_data
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
