import os, requests, html, re
from bs4 import BeautifulSoup
from datetime import datetime

# === CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
QLD_URL = "https://www.qbcc.qld.gov.au/news-resources/news"

def send_telegram(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}, timeout=30)

def get_qld_data():
    print("🔍 Triple-checking QBCC News Feed...")
    results = []
    seen_links = set()
    
    session = requests.Session()
    # High-authority header to avoid being flagged as a bot
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com"
    })

    try:
        r = session.get(QLD_URL, timeout=20)
        soup = BeautifulSoup(r.content, "html.parser")
        
        # METHOD 1: Target the 2026 "Latest News" cards
        items = soup.select('.views-row, article, .news-item, .field-content')
        
        # METHOD 2: Fallback to all H2/H3 headers in case Method 1 returns empty
        if not items:
            items = soup.find_all(['h2', 'h3'])

        for item in items:
            link_tag = item if item.name == 'a' else item.find('a', href=True)
            if not link_tag: continue
            
            link = link_tag['href']
            # Skip non-news links
            if any(x in link for x in ["#", "/user", "/about-us", "facebook", "twitter"]):
                continue

            full_url = link if link.startswith("http") else f"https://www.qbcc.qld.gov.au{link}"
            if full_url in seen_links: continue

            # Clean the text
            text = link_tag.get_text(" ").strip()
            # Remove "Read More", Dates, and weird spacing
            clean_title = re.sub(r'(Read More|Article|News|Campaign|\| \d+ \w+ \d{4})', '', text, flags=re.IGNORECASE).strip()
            clean_title = ' '.join(clean_title.split())

            if len(clean_title) > 15:
                results.append(f"• <b>[📰 QLD]</b> {html.escape(clean_title)}\n🔗 {full_url}")
                seen_links.add(full_url)

    except Exception as e:
        print(f"Scraper error: {e}")
            
    return results

def main():
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    
    headlines = get_qld_data()
    header = f"☀️ <b>QBCC Queensland Update</b>\n📅 {datetime.now().strftime('%d %b %Y')}\n\n"
    
    # If scraper finds nothing, we provide direct one-tap links
    if headlines:
        body = "\n\n".join(headlines[:6])
    else:
        body = (
            "⚠️ <b>Bot detection triggered. Tap to view manually:</b>\n"
            "➡️ <a href='https://www.qbcc.qld.gov.au/news-resources/news'>Latest News & Warnings</a>\n"
            "➡️ <a href='https://www.qbcc.qld.gov.au/news-resources/media-releases'>Media Releases</a>"
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
