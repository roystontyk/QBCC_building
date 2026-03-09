import os, requests, html
from bs4 import BeautifulSoup
from datetime import datetime

# === CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
QLD_URL = "https://www.qbcc.qld.gov.au/news-resources/news"

def send_telegram(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=30)

def get_qld_data():
    print("🔍 Attempting Stealth Scrape of QBCC...")
    results = []
    
    # Use a Session to handle cookies/handshakes like a real browser
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/"
    })

    try:
        r = session.get(QLD_URL, timeout=20)
        # If the site blocks us, this will help us see why in the logs
        print(f"Response Code: {r.status_code}")
        
        soup = BeautifulSoup(r.content, "html.parser")
        
        # In 2026, QBCC wraps news in <h3> tags inside the 'views-element-container'
        news_titles = soup.find_all(['h3', 'h2'], class_=False) # They often use naked headers for news
        
        if not news_titles:
            # Fallback: Just grab every link in the main content area
            main_content = soup.find('main')
            news_titles = main_content.find_all('a', href=True) if main_content else []

        for item in news_titles:
            # If item is a header, find the link inside it
            link_tag = item if item.name == 'a' else item.find('a', href=True)
            if not link_tag: continue
            
            title = link_tag.get_text().strip()
            link = link_tag['href']
            
            # Filter out utility links
            if len(title) < 15 or link.startswith('#') or "node/" in link:
                continue
            
            full_url = link if link.startswith("http") else f"https://www.qbcc.qld.gov.au{link}"
            
            # Avoid duplicates
            entry = f"• <b>[📰 QLD]</b> {html.escape(title)}\n🔗 {full_url}"
            if entry not in results:
                results.append(entry)

    except Exception as e:
        print(f"Scraper error: {e}")
            
    return results

def main():
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    
    headlines = get_qld_data()
    header = f"☀️ <b>QBCC Queensland Update</b>\n📅 {datetime.now().strftime('%d %b %Y')}\n\n"
    
    # If the scraper still finds nothing, we provide a "Quick Access" list 
    # so you can at least click through manually from Telegram.
    if headlines:
        body = "\n\n".join(headlines[:8])
    else:
        body = (
            "⚠️ <b>Direct Access (Bot Blocked):</b>\n"
            "• <a href='https://www.qbcc.qld.gov.au/news-resources/news'>Latest News Feed</a>\n"
            "• <a href='https://www.qbcc.qld.gov.au/news-resources/media-releases'>Media Releases</a>\n"
            "• <a href='https://www.qbcc.qld.gov.au/news-resources/public-warnings'>Public Warnings</a>"
        )

    footer = (
        "\n\n---\n"
        "<b>📂 QLD PERMANENT REGISTERS:</b>\n"
        "🚫 <a href='https://www.qbcc.qld.gov.au/about-us/our-lists-registers/excluded-individuals-register'>Excluded Individuals (Banned)</a>\n"
        "📑 <a href='https://www.qbcc.qld.gov.au/about-us/our-lists-registers/adjudication-decision-register'>Adjudication Decisions</a>"
    )

    send_telegram(header + body + footer)

if __name__ == "__main__":
    main()
