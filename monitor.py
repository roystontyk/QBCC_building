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
    print("🔍 Cleaning up QLD News Feed...")
    results = []
    seen_links = set()
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    })

    try:
        r = session.get(QLD_URL, timeout=20)
        soup = BeautifulSoup(r.content, "html.parser")
        
        # Target the news items specifically
        # QBCC uses 'views-row' for each news card
        rows = soup.select('.views-row')
        
        for row in rows:
            link_tag = row.find('a', href=True)
            if not link_tag: continue
            
            # Clean up the title: remove "Read More", extra dates, and "Article |" prefixes
            raw_text = link_tag.get_text(separator=' ').strip()
            # This regex clears out the "Read More" and the duplicate date/type info
            clean_title = re.sub(r'(Read More|Article|News|Campaign|\| \d+ \w+ \d{4})', '', raw_text, flags=re.IGNORECASE).strip()
            # Collapse multiple spaces
            clean_title = ' '.join(clean_title.split())
            
            link = link_tag['href']
            full_url = link if link.startswith("http") else f"https://www.qbcc.qld.gov.au{link}"
            
            # Skip noise and duplicates
            if len(clean_title) < 15 or full_url in seen_links or "/news-resources" in full_url:
                continue
            
            results.append(f"• <b>[📰 QLD]</b> {html.escape(clean_title)}\n🔗 {full_url}")
            seen_links.add(full_url)

    except Exception as e:
        print(f"Scraper error: {e}")
            
    return results

def main():
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    
    headlines = get_qld_data()
    header = f"☀️ <b>QBCC Queensland Update</b>\n📅 {datetime.now().strftime('%d %b %Y')}\n\n"
    
    if headlines:
        body = "\n\n".join(headlines[:6]) # Show top 6 latest clean items
    else:
        body = "<i>No new QLD headlines found today.</i>"

    footer = (
        "\n\n---\n"
        "<b>📂 QLD PERMANENT REGISTERS:</b>\n"
        "🚫 <a href='https://www.qbcc.qld.gov.au/about-us/our-lists-registers/excluded-individuals-register'>Excluded Individuals (Banned)</a>\n"
        "📑 <a href='https://www.qbcc.qld.gov.au/about-us/our-lists-registers/adjudication-decision-register'>Adjudication Decisions</a>"
    )

    send_telegram(header + body + footer)

if __name__ == "__main__":
    main()
