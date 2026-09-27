#!/usr/bin/env python3
import json
import time
import re
from playwright.sync_api import sync_playwright
from datetime import datetime

API_CHANNELS_URL = "https://core-api.kablowebtv.com/api/channels"

def generate_m3u():
    try:
        print("🌐 Gerçekçi tarayıcı profili başlatılıyor ve tvheryerde.com açılıyor...")
        captured_headers = None
        cookies_list = None
        
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
            
            # Regex ile eyJ... içeren geçerli JWT token'ı yakalama
            def handle_request(request):
                nonlocal captured_headers
                if "core-api.kablowebtv.com" in request.url and not captured_headers:
                    headers = request.headers
                    auth_header = headers.get("authorization", "")
                    
                    # Regex deseni ile eyJ ile başlayan JWT yapısını ara
                    jwt_pattern = re.compile(r'eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+')
                    match = jwt_pattern.search(auth_header)
                    
                    if match:
                        captured_headers = dict(headers)
                        pure_token = match.group(0)
                        print(f"🔑 [DEBUG] Regex ile geçerli JWT Token yakalandı: {pure_token[:30]}...")

            page.on("request", handle_request)

            # Sayfaya git
            page.goto("https://tvheryerde.com", timeout=60000)
            
            # Token'ın yakalanması için bekle
            start_time = time.time()
            while not captured_headers and time.time() - start_time < 15:
                page.wait_for_timeout(500)
                
            if not captured_headers:
                raise ValueError("Regex ile eşleşen geçerli bir JWT token yakalanamadı!")
            
            # Tarayıcı çerezlerini al ve başlığa ekle
            cookies_list = context.cookies()
            cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookies_list])
            if cookie_string:
                captured_headers["Cookie"] = cookie_string
                print("🍪 [DEBUG] Tarayıcı çerezleri başlığa eklendi.")
            
            print("📡 Yakalanan tam başlıklar ve çerezler ile /api/channels adresine istek atılıyor...")
            
            # Yakalanan orijinal başlıklar ve çerezleri kullanarak fetch at
            api_response = page.evaluate("""async ({ url, reqHeaders }) => {
                const res = await fetch(url, {
                    method: 'GET',
                    headers: reqHeaders
                });
                return await res.json();
            }""", {"url": API_CHANNELS_URL, "reqHeaders": captured_headers})
            
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
