#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROFESSIONAL FAUCET CLAIM BOT v3.0
- xEvil Captcha Çözücü Entegrasyonu
- Cloudflare Bypass (cloudscraper)
- Proxy Desteği (HTTP/SOCKS5)
- Otomatik PHPSESSID Yönetimi
- Çoklu Site Desteği
- ThreadPoolExecutor ile Paralel Claim
- Detaylı Loglama
- Telegram Bildirimleri
"""

import requests
import time
import re
import os
import json
import sys
import random
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Cloudflare bypass için
try:
    import cloudscraper
    SCRAPER_AVAILABLE = True
except ImportError:
    SCRAPER_AVAILABLE = False
    print("cloudscraper yüklü değil. pip install cloudscraper")

# --- RENKLER ---
G = '\033[1;32m'
R = '\033[1;31m'
Y = '\033[1;33m'
C = '\033[1;36m'
W = '\033[0m'
M = '\033[1;35m'
B = '\033[1;34m'

# --- AYARLAR ---
CONFIG_FILE = "config.json"
PROXY_FILE = "proxies.txt"
LOG_FILE = "claims.log"
SOLVER_URL = "http://157.180.15.203"
SITE_KEY = "6LfwaSgTAAAAAJJNz6oAdimVHmIe3s4fHj4D0at4"

# Telegram bildirimleri (isteğe bağlı)
TELEGRAM_BOT_TOKEN = ""  # Buraya bot token
TELEGRAM_CHAT_ID = ""    # Buraya chat ID

# Coin listeleri
FREE_COINS = [
    "bitcoin", "dogecoin", "litecoin", "tron", "tether", 
    "ethereum", "bnb", "solana", "usdc", "ripple"
]

BEE_COINS = [
    "btcb", "doge", "trx", "usdt", "eth", "bnb", 
    "sol", "usdc", "xrp", "ton"
]

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- YARDIMCI FONKSİYONLAR ---

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner(cycle=0, mode="FREE", email="", proxy_count=0):
    clear()
    print(f"{C}{'═'*70}{W}")
    print(f"{G}╔═╗╦  ╔═╗╦╔╗╔╔╦╗╔═╗╦═╗  ╔═╗╔═╗╦ ╦╔═╗╔═╗╔╦╗  ╔╗ ╔═╗╔╦╗{W}")
    print(f"{G}║  ║  ╠═╣║║║║ ║║║╣ ╠╦╝  ╠╣ ╠═╣║ ║║  ║╣  ║   ╠╩╗║ ║ ║ {W}")
    print(f"{G}╚═╝╩═╝╩ ╩╩╝╚╝═╩╝╚═╝╩╚═  ╚  ╩ ╩╚═╝╚═╝╚═╝ ╩   ╚═╝╚═╝ ╩ {W}")
    print(f"{C}{'═'*70}{W}")
    print(f"{B}► MOD: {G}{mode}{W}   {B}► CYCLE: {Y}{cycle}{W}   {B}► PROXIES: {M}{proxy_count}{W}")
    print(f"{B}► USER: {C}{email}{W}   {B}► TIME: {Y}{datetime.now().strftime('%H:%M:%S')}{W}")
    print(f"{C}{'═'*70}{W}\n")

def load_proxies():
    """Proxy listesini yükle"""
    proxies = []
    if os.path.exists(PROXY_FILE):
        with open(PROXY_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    proxies.append(line)
    return proxies

def get_random_proxy(proxies):
    """Rastgele proxy döndür"""
    if proxies:
        proxy = random.choice(proxies)
        return {
            'http': proxy,
            'https': proxy
        }
    return None

def get_config():
    """Config dosyasını yükle veya oluştur"""
    default_config = {
        "email": "",
        "api_key": "",
        "phpsessid": "",
        "mode": "free",
        "use_proxy": False,
        "telegram_enabled": False
    }
    
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Eksik alanları ekle
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
    
    print(f"{Y}[!] İlk kurulum{W}")
    config = default_config.copy()
    config['email'] = input(f"{C}► FaucetPay Email: {W}").strip()
    config['api_key'] = input(f"{C}► xEvil API Key: {W}").strip()
    config['mode'] = input(f"{C}► Mode (free/paid) [free]: {W}").strip().lower() or "free"
    config['use_proxy'] = input(f"{C}► Proxy kullanılsın mı? (y/n) [n]: {W}").strip().lower() == 'y'
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config

def send_telegram(message):
    """Telegram'a bildirim gönder"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(url, data=data, timeout=10)
    except:
        pass

def solve_captcha_xevil(api_key, page_url):
    """xEvil API ile reCAPTCHA çöz"""
    sys.stdout.write(f"\r{Y}[⚡] Captcha çözülüyor...{W}")
    sys.stdout.flush()
    
    try:
        # API'ye istek gönder
        params = {
            'key': api_key,
            'method': 'userrecaptcha',
            'pageurl': page_url,
            'sitekey': SITE_KEY,
            'json': 1
        }
        
        resp = requests.get(f"{SOLVER_URL}/in.php", params=params, timeout=30)
        data = resp.json()
        
        if data.get('status') == 1:
            captcha_id = data.get('request')
            
            # Çözümü bekle
            for i in range(40):  # Max 2 dakika
                time.sleep(3)
                result = requests.get(
                    f"{SOLVER_URL}/res.php",
                    params={'key': api_key, 'action': 'get', 'id': captcha_id, 'json': 1},
                    timeout=30
                ).json()
                
                if result.get('status') == 1:
                    token = result.get('request')
                    sys.stdout.write(f"\r{G}[✓] Captcha çözüldü!{W}      \n")
                    logger.info(f"Captcha çözüldü: {page_url}")
                    return token
                
                elif result.get('request') == 'CAPCHA_NOT_READY':
                    continue
                else:
                    logger.error(f"Captcha hatası: {result}")
                    break
        
        sys.stdout.write(f"\r{R}[✗] Captcha zaman aşımı{W}\n")
        return None
        
    except Exception as e:
        sys.stdout.write(f"\r{R}[✗] Captcha hatası: {str(e)[:50]}{W}\n")
        logger.error(f"Captcha exception: {e}")
        return None

def create_session(use_proxy=False, proxies_list=None):
    """Session oluştur (Cloudflare bypass veya normal)"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    if SCRAPER_AVAILABLE:
        session = cloudscraper.create_scraper()
    else:
        session = requests.Session()
    
    session.headers.update(headers)
    
    # Proxy ayarla
    if use_proxy and proxies_list:
        proxy = get_random_proxy(proxies_list)
        if proxy:
            session.proxies.update(proxy)
            logger.debug(f"Proxy kullanılıyor: {proxy}")
    
    return session

def claim_free_coin(coin, email, api_key, proxies_list, use_proxy):
    """ClaimFreeCoins.io'da claim yap"""
    
    session = create_session(use_proxy, proxies_list)
    url = f"https://claimfreecoins.io/{coin}-faucet/?r=arasarathinam3@gmail.com"
    
    try:
        # Sayfayı al
        resp = session.get(url, timeout=20)
        
        # Cloudflare kontrolü
        if 'cf-ray' in resp.headers or 'challenge' in resp.text.lower():
            logger.warning(f"{coin}: Cloudflare tespit edildi")
            return f"{R}⛔ CLOUDFLARE{W}", False
        
        # Session token bul
        patterns = [
            r'name="session-token" value="([^"]+)"',
            r'session-token" value="([^"]+)"',
            r'name=session-token value=([^\s>]+)'
        ]
        
        session_token = None
        for pattern in patterns:
            match = re.search(pattern, resp.text)
            if match:
                session_token = match.group(1)
                break
        
        if not session_token:
            logger.error(f"{coin}: Session token bulunamadı")
            return f"{R}❌ TOKEN BULUNAMADI{W}", False
        
        # Captcha çöz
        captcha_token = solve_captcha_xevil(api_key, url)
        if not captcha_token:
            return f"{R}❌ CAPTCHA ÇÖZÜLEMEDİ{W}", False
        
        # Claim isteği
        payload = {
            'session-token': session_token,
            'address': email,
            'captcha': 'recaptcha',
            'g-recaptcha-response': captcha_token,
            'login': 'Verify Captcha'
        }
        
        # Rastgele bekleme
        time.sleep(random.uniform(1, 3))
        
        post_resp = session.post(url, data=payload, timeout=20)
        body = post_resp.text.lower()
        
        # Başarı kontrolü
        success_phrases = [
            "satoshi was sent", "successfully sent", "claim confirmed",
            "you have claimed", "reward sent", "faucet claim successful",
            "claimed successfully", "your reward"
        ]
        
        if any(phrase in body for phrase in success_phrases):
            # Miktarı bul
            amount_patterns = [
                r'(\d+(?:\.\d+)?)\s*(satoshi|btc|doge|ltc|trx|usdt|eth|bnb|sol)',
                r'(\d+)\s*satoshi',
                r'received\s*(\d+(?:\.\d+)?)'
            ]
            
            amount = "?"
            unit = "Sat"
            for pattern in amount_patterns:
                amt_match = re.search(pattern, body)
                if amt_match:
                    amount = amt_match.group(1)
                    if len(amt_match.groups()) > 1:
                        unit = amt_match.group(2)
                    break
            
            logger.info(f"{coin}: BAŞARILI - {amount} {unit}")
            send_telegram(f"✅ <b>{coin.upper()}</b> claim başarılı!\n💰 Miktar: {amount} {unit}")
            return f"{G}✅ BAŞARILI: {amount} {unit}{W}", True
        
        elif "already claimed" in body or "wait" in body or "next claim" in body:
            # Zaman bilgisini bul
            time_match = re.search(r'(\d+)\s*(minutes?|hours?|seconds?)', body)
            wait_time = time_match.group(0) if time_match else "bilinmiyor"
            logger.info(f"{coin}: Zamanı gelmedi - {wait_time}")
            return f"{Y}⏳ BEKLE: {wait_time}{W}", False
        
        elif "invalid captcha" in body:
            logger.warning(f"{coin}: Geçersiz captcha")
            return f"{R}❌ GEÇERSİZ CAPTCHA{W}", False
        
        else:
            # Hata mesajını bul
            error_match = re.search(r'<div[^>]*alert[^>]*>(.*?)</div>', body, re.DOTALL)
            if error_match:
                error_msg = re.sub(r'<[^>]+>', '', error_match.group(1)).strip()[:50]
                logger.error(f"{coin}: {error_msg}")
                return f"{R}❌ {error_msg}{W}", False
            
            logger.error(f"{coin}: Bilinmeyen hata")
            return f"{R}❌ BİLİNMEYEN HATA{W}", False
            
    except requests.exceptions.Timeout:
        logger.error(f"{coin}: Zaman aşımı")
        return f"{R}⏱️ ZAMAN AŞIMI{W}", False
    except Exception as e:
        logger.error(f"{coin}: {str(e)[:50]}")
        return f"{R}⛔ HATA: {str(e)[:30]}{W}", False

def claim_bee_coin(coin, email, api_key, phpsessid, proxies_list, use_proxy):
    """BeeFaucet.org'da claim yap"""
    
    session = create_session(use_proxy, proxies_list)
    if phpsessid:
        session.cookies.set('PHPSESSID', phpsessid)
    
    url = f"https://beefaucet.org/{coin}-faucet/?r=anilodhi2019@gmail.com"
    
    try:
        # Sayfayı al
        resp = session.get(url, timeout=20)
        
        # Yeni PHPSESSID varsa al
        new_sessid = session.cookies.get('PHPSESSID')
        if new_sessid and new_sessid != phpsessid:
            # Config'i güncelle
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                config['phpsessid'] = new_sessid
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(config, f, indent=2)
                logger.info(f"Yeni PHPSESSID kaydedildi: {new_sessid[:10]}...")
        
        # Cloudflare kontrolü
        if 'cf-ray' in resp.headers or 'challenge' in resp.text.lower():
            logger.warning(f"{coin}: Cloudflare tespit edildi")
            return f"{R}⛔ CLOUDFLARE{W}", False, new_sessid
        
        # Session token bul
        token_match = re.search(r'name="session-token" value="([^"]+)"', resp.text)
        if not token_match:
            token_match = re.search(r'session-token" value="([^"]+)"', resp.text)
        
        if not token_match:
            logger.error(f"{coin}: Session token bulunamadı")
            return f"{R}❌ TOKEN BULUNAMADI{W}", False, new_sessid
        
        session_token = token_match.group(1)
        
        # Captcha çöz
        captcha_token = solve_captcha_xevil(api_key, url)
        if not captcha_token:
            return f"{R}❌ CAPTCHA ÇÖZÜLEMEDİ{W}", False, new_sessid
        
        # Claim isteği
        payload = {
            'session-token': session_token,
            'address': email,
            'captcha': 'recaptcha',
            'g-recaptcha-response': captcha_token,
            'login': 'Verify Captcha'
        }
        
        time.sleep(random.uniform(1, 3))
        
        post_resp = session.post(url, data=payload, timeout=20)
        body = post_resp.text.lower()
        
        # Başarı kontrolü
        success_phrases = [
            "satoshi was sent", "successfully sent", "claim confirmed",
            "you have claimed", "reward sent", "faucet claim successful"
        ]
        
        if any(phrase in body for phrase in success_phrases):
            amount = "?"
            amt_match = re.search(r'(\d+(?:\.\d+)?)\s*(satoshi|btc|doge|trx|usdt)', body)
            if amt_match:
                amount = amt_match.group(1)
                unit = amt_match.group(2)
            else:
                unit = "Sat"
            
            logger.info(f"{coin}: BAŞARILI - {amount} {unit}")
            send_telegram(f"✅ <b>{coin.upper()}</b> (Bee) claim başarılı!\n💰 Miktar: {amount} {unit}")
            return f"{G}✅ BAŞARILI: {amount} {unit}{W}", True, new_sessid
        
        elif "already claimed" in body or "wait" in body:
            time_match = re.search(r'(\d+)\s*(minutes?|hours?|seconds?)', body)
            wait_time = time_match.group(0) if time_match else "bilinmiyor"
            logger.info(f"{coin}: Zamanı gelmedi - {wait_time}")
            return f"{Y}⏳ BEKLE: {wait_time}{W}", False, new_sessid
        
        elif "invalid captcha" in body:
            logger.warning(f"{coin}: Geçersiz captcha")
            return f"{R}❌ GEÇERSİZ CAPTCHA{W}", False, new_sessid
        
        else:
            logger.error(f"{coin}: Bilinmeyen hata")
            return f"{R}❌ BİLİNMEYEN HATA{W}", False, new_sessid
            
    except Exception as e:
        logger.error(f"{coin}: {str(e)[:50]}")
        return f"{R}⛔ HATA: {str(e)[:30]}{W}", False, phpsessid

def main():
    """Ana fonksiyon"""
    
    print(f"{C}FAUCET CLAIM BOT v3.0 BAŞLATILIYOR...{W}\n")
    
    # Config yükle
    config = get_config()
    email = config.get('email', '')
    api_key = config.get('api_key', '')
    mode = config.get('mode', 'free')
    use_proxy = config.get('use_proxy', False)
    
    # Proxy'leri yükle
    proxies_list = []
    if use_proxy:
        proxies_list = load_proxies()
        print(f"{G}[✓] {len(proxies_list)} proxy yüklendi{W}\n")
    
    # Coin listelerini belirle
    if mode == "paid":
        free_coins = FREE_COINS
        bee_coins = BEE_COINS
    else:
        free_coins = FREE_COINS[:5]  # İlk 5 coin
        bee_coins = BEE_COINS[:4]    # İlk 4 coin
    
    phpsessid = config.get('phpsessid', '')
    cycle = 1
    
    print(f"{C}{'═'*70}{W}")
    print(f"{G}🚀 BOT BAŞLADI{W}")
    print(f"{B}► Email: {C}{email}{W}")
    print(f"{B}► Mod: {Y}{mode.upper()}{W}")
    print(f"{B}► Proxy: {G if use_proxy else R}{use_proxy}{W}")
    print(f"{B}► Free Coins: {M}{len(free_coins)}{W}")
    print(f"{B}► Bee Coins: {M}{len(bee_coins)}{W}")
    print(f"{C}{'═'*70}{W}\n")
    
    send_telegram(f"🤖 <b>Bot Başladı</b>\n👤 {email}\n⚙️ Mod: {mode.upper()}")
    
    time.sleep(2)
    
    while True:
        banner(cycle, mode.upper(), email, len(proxies_list))
        
        # ========== CLAIM FREE COINS ==========
        print(f"{C}🌍 ClaimFreeCoins.io{W}")
        print(f"{'─'*70}")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for coin in free_coins:
                future = executor.submit(
                    claim_free_coin, coin, email, api_key, proxies_list, use_proxy
                )
                futures[future] = coin
                time.sleep(0.2)  # Rate limiting
            
            for future in as_completed(futures):
                coin = futures[future]
                result, success = future.result()
                print(f"  {W}► {coin.upper():12} {result}")
        
        # ========== CLAIM BEE COINS ==========
        print(f"\n{C}🐝 BeeFaucet.org{W}")
        print(f"{'─'*70}")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for coin in bee_coins:
                future = executor.submit(
                    claim_bee_coin, coin, email, api_key, phpsessid, proxies_list, use_proxy
                )
                futures[future] = coin
                time.sleep(0.2)
            
            for future in as_completed(futures):
                coin = futures[future]
                result, success, new_sessid = future.result()
                if new_sessid:
                    phpsessid = new_sessid
                print(f"  {W}► {coin.upper():12} {result}")
        
        # ========== BEKLEME ==========
        wait_minutes = 5
        print(f"\n{Y}⏳ {wait_minutes} dakika bekleniyor...{W}")
        logger.info(f"Cycle {cycle} tamamlandı. {wait_minutes} dakika bekleniyor.")
        
        for i in range(wait_minutes * 60, 0, -1):
            mins = i // 60
            secs = i % 60
            sys.stdout.write(f"\r{Y}► Sonraki cycle: {mins:02d}:{secs:02d}{W} ")
            sys.stdout.flush()
            time.sleep(1)
        
        print("\n")
        cycle += 1

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{R}🛑 Bot durduruldu.{W}")
        logger.info("Bot kullanıcı tarafından durduruldu.")
        send_telegram("🛑 Bot durduruldu.")
        sys.exit()
    except Exception as e:
        print(f"\n{R}⛔ Kritik hata: {e}{W}")
        logger.critical(f"Kritik hata: {e}")
        sys.exit(1)
