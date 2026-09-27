#!/usr/bin/env python3
import json
from playwright.sync_api import sync_playwright
from datetime import datetime

API_CHANNELS_URL = "https://core-api.kablowebtv.com/api/channels"

def generate_m3u():
    try:
        print("🌐 Tarayıcı başlatılıyor...")
        captured_json = None
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # 1. Önce ana sayfaya gidip oturumun/çerezlerin oluşmasını sağlıyoruz
            print("🌐 tvheryerde.com ana sayfasına bağlanılıyor...")
            page.goto("https://tvheryerde.com", timeout=60000)
            page.wait_for_timeout(5000) # Oturumun oturması için bekle
            
            # 2. Ağ trafiğinden /api/channels isteğinin JSON yanıtını direkt yakalayalım
            def handle_response(response):
                nonlocal captured_json
                if "/api/channels" in response.url:
                    try:
                        data = response.json()
                        if data.get('IsSucceeded'):
                            captured_json = data
                            print("🎯 [DEBUG] Channels API verisi doğrudan yakalandı!")
                    except Exception:
                        pass

            page.on("response", handle_response)

            # 3. Şimdi doğrudan API adresine giderek sitenin kendi oturumuyla tetiklenmesini sağlıyoruz
            print("📡 Doğrudan API adresine gidiliyor...")
            page.goto(API_CHANNELS_URL, timeout=30000)
            page.wait_for_timeout(3000)
            
            # Eğer yukarıdaki yakalamazsa, sayfanın body'sindeki metni JSON olarak almayı deneyelim
            if not captured_json:
                try:
                    body_text = page.inner_text("body")
                    parsed = json.loads(body_text)
                    if parsed.get('IsSucceeded'):
                        captured_json = parsed
                        print("🎯 [DEBUG] API verisi sayfa içeriğinden okundu!")
                except Exception:
                    pass
            
            browser.close()
            
        if not captured_json or not captured_json.get('Data', {}).get('AllChannels'):
            raise ValueError("API'den geçerli kanal verisi alınamadı.")
        
        data = captured_json
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
