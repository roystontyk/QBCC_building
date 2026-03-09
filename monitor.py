import os, requests, html
from bs4 import BeautifulSoup
from datetime import datetime

# === CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Primary News Page
QLD_URL = "https://www.qbcc.qld.gov.au/news-resources/news"

def send_telegram(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=30)
    print(f"Telegram status: {r.status_code}")

def get_qld_data():
    print("🔍 Scraping QBCC News (March 2026 Layout)...")
    results = []
    seen_links = set()

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(QLD_URL, headers=headers, timeout=20)
        soup = BeautifulSoup(r.content, "html.parser")
        
        # 2026 Target: Look for news items within list views or tables
        # The site currently uses 'views-row' and specific link structures for news
        news_items = soup.select('.views-row, .views-field-title, article')
        
        for item in news_items:
            link_tag = item.find('a', href=True)
            if not link_tag: continue
            
            title = link_tag.get_text().strip()
            link = link_tag['href']
            
            # Filter out navigation/junk
            if len(title) < 12 or any(x in title.lower() for x in ["read more", "view all", "contact"]):
                continue
                
            full_url = link if link.startswith("http") else f"https://www.qbcc.qld.gov.au{link}"
            
            if full_url not in seen_links:
                # Add a visual tag based on URL or text
                tag = "📰 NEWS"
                if "media-release" in full_url: tag = "📢 MEDIA"
                elif "warning" in full_url: tag = "⚠️ WARNING"
                
                results.append(f"• <b>[{tag}]</b> {html.escape(title)}\n🔗 {full_url}")
                seen_links.add(full_url)

    except Exception as e:
        print(f"Scraper error: {e}")
            
    return results

def main():
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Error: Missing Telegram Environment Variables!")
        return

    headlines = get_qld_data()
    print(f"Found {len(headlines)} items.")

    header = f"☀️ <b>QBCC Queensland Update</b>\n📅 {datetime.now().strftime('%d %b %Y')}\n\n"
    
    if headlines:
        body = "\n\n".join(headlines[:10]) # Top 10 latest
    else:
        body = "<i>No news items found. The site structure may have changed.</i>"

    footer = (
        "\n\n---\n"
        "<b>📂 QLD PERMANENT REGISTERS:</b>\n"
        "🚫 <b>Excluded Individuals (Banned):</b>\n"
        "https://www.qbcc.qld.gov.au/about-us/our-lists-registers/excluded-individuals-register\n\n"
        "📑 <b>Adjudication Decisions:</b>\n"
        "https://www.qbcc.qld.gov.au/about-us/our-lists-registers/adjudication-decision-register"
    )

    send_telegram(header + body + footer)

if __name__ == "__main__":
    main()
