#!/usr/bin/env python3
import json
import time
from playwright.sync_api import sync_playwright
from datetime import datetime

API_CHANNELS_URL = "https://core-api.kablowebtv.com/api/channels"

def generate_m3u():
    try:
        print("🌐 Tarayıcı başlatılıyor ve tvheryerde.com açılıyor...")
        captured_headers = None
        
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
            
            # 1. Sitenin core-api'ye attığı ilk başarılı isteğin TÜM header'larını yakala
            def handle_request(request):
                nonlocal captured_headers
                if "core-api.kablowebtv.com" in request.url and not captured_headers:
                    headers = request.headers
                    if "authorization" in headers:
                        captured_headers = headers
                        print("🔑 [DEBUG] Orijinal API istek header'ları ve taze token başarıyla yakalandı!")

            page.on("request", handle_request)

            # Sayfaya git
            print("🌐 Sayfa yükleniyor...")
            page.goto("https://tvheryerde.com", timeout=60000)
            
            # Header'ların yakalanması için kısa bir süre bekle
            start_time = time.time()
            while not captured_headers and time.time() - start_time < 15:
                page.wait_for_timeout(500)
                
            if not captured_headers:
                raise ValueError("API istek header'ları (Authorization vb.) yakalanamadı!")
            
            print("📡 Yakalanan orijinal headerlar ile /api/channels adresine istek atılıyor...")
            
            # 2. Sitenin kendi kullandığı tüm orijinal header'ları fetch içine vererek kanalları çek
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
