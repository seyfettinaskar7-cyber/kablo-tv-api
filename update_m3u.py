#!/usr/bin/env python3
import requests
import json
from datetime import datetime

API_CHANNELS_URL = "https://core-api.kablowebtv.com/api/channels"

def generate_m3u():
    try:
        print("🌐 Tarayıcı atlanıyor, doğrudan core-api.kablowebtv.com adresine bağlanılıyor...")
        
        # Olası platform başlığı alternatifleri
        platforms_to_try = ["web", "desktop", "browser", "html5", "pc"]
        
        data = None
        for platform in platforms_to_try:
            print(f"🔍 Denenen Platform Parametresi: '{platform}'")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Referer": "https://tvheryerde.com/",
                "Origin": "https://tvheryerde.com",
                "Platform": platform,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
            }
            
            try:
                response = requests.get(API_CHANNELS_URL, headers=headers, timeout=10)
                if response.status_code == 200:
                    json_data = response.json()
                    if json_data.get('IsSucceeded'):
                        data = json_data
                        print(f"🎉 Başarılı! Doğru platform parametresi bulundu: '{platform}'")
                        break
                    else:
                        print(f"   ↳ API Reddetti: {json_data.get('Label')} - {json_data.get('Message')}")
                else:
                    print(f"   ↳ HTTP Durum Kodu: {response.status_code}")
            except Exception as e:
                print(f"   ↳ İstek hatası: {str(e)}")
                
        if not data or not data.get('Data', {}).get('AllChannels'):
            raise ValueError("Hiçbir platform parametresi ile geçerli API yanıtı alınamadı.")
        
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
