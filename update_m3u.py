#!/usr/bin/env python3
import json
import time
from playwright.sync_api import sync_playwright
from datetime import datetime

API_CHANNELS_URL = "https://core-api.kablowebtv.com/api/channels"

def generate_m3u():
    try:
        print("🌐 Gerçekçi tarayıcı profili başlatılıyor...")
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
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="tr-TR",
                timezone_id="Europe/Istanbul",
                extra_http_headers={
                    "Referer": "https://tvheryerde.com/",
                    "Origin": "https://tvheryerde.com",
                    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
                }
            )
            
            # Gerçek kullanıcı parmak izi (Stealth) enjeksiyonu
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
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)
            
            page = context.new_page()
            
            # Ağ trafiğindeki /api/channels yanıtını doğrudan dinle ve yakala
            def handle_response(response):
                nonlocal captured_data
                if "/api/channels" in response.url:
                    try:
                        json_data = response.json()
                        if json_data.get('IsSucceeded'):
                            captured_data = json_data
                            print("🎯 [DEBUG] Channels API yanıtı doğrudan ağ trafiğinden yakalandı!")
                    except Exception:
                        pass

            page.on("response", handle_response)

            # Doğrudan canlı TV veya kanalların yüklendiği sayfaya bağlan
            print("🌐 tvheryerde.com/canli-tv sayfasına bağlanılıyor...")
            page.goto("https://tvheryerde.com/canli-tv", timeout=60000)
            
            # Sitenin arayüzünün yüklenmesi ve API isteğini tetiklemesi için bekle
            start_time = time.time()
            while not captured_data and time.time() - start_time < 20:
                page.wait_for_timeout(1000)
                # Eğer ilk başta yakalanamazsa sayfada hafifçe aşağı kaydırarak tetikleyelim
                if not captured_data and time.time() - start_time > 5:
                    try:
                        page.mouse.wheel(0, 300)
                    except Exception:
                        pass

            browser.close()
            
        if not captured_data or not captured_data.get('Data', {}).get('AllChannels'):
            raise ValueError("API yanıtı ağ trafiğinden yakalanamadı.")
        
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
