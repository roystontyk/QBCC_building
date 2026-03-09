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
    print("🔍 Fetching Headings Only...")
    results = []
    seen_links = set()
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0"
    })

    try:
        r = session.get(QLD_URL, timeout=20)
        soup = BeautifulSoup(r.content, "html.parser")
        
        # Target the specific news titles in the cards
        # QBCC structure: the H3 usually contains the clean title
        news_cards = soup.select('.views-row')
        
        for card in news_cards:
            title_element = card.find('h3') or card.find('h2')
            link_tag = card.find('a', href=True)
            
            if not title_element or not link_tag:
                continue
            
            # Extract just the heading text
            raw_title = title_element.get_text().strip()
            
            # Clean "Article | Date" or duplicate prefixes
            clean_title = re.sub(r'(Article|News|Campaign|\| \d+ \w+ \d{4})', '', raw_title, flags=re.IGNORECASE).strip()
            
            link = link_tag['href']
            full_url = link if link.startswith("http") else f"https://www.qbcc.qld.gov.au{link}"
            
            if full_url not in seen_links and len(clean_title) > 10:
                results.append(f"• <b>[📰 QLD]</b> {html.escape(clean_title)}\n🔗 {full_url}")
                seen_links.add(full_url)

    except Exception as e:
        print(f"Scraper error: {e}")
            
    return results

def main():
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    
    headlines = get_qld_data()
    header = f"☀️ <b>QBCC Queensland Update</b>\n📅 {datetime.now().strftime('%d %b %Y')}\n\n"
    
    # Since it's only headings, we can fit more (top 15)
    if headlines:
        body = "\n\n".join(headlines[:15])
    else:
        body = "<i>No new QLD headings found today.</i>"

    footer = (
        "\n\n---\n"
        "<b>📂 QLD PERMANENT REGISTERS:</b>\n"
        "🚫 <a href='https://my.qbcc.qld.gov.au/myQBCC/s/suspended-registers'>Suspended Registers</a>\n"
        "❌ <a href='https://my.qbcc.qld.gov.au/myQBCC/s/cancelled-registers'>Cancelled Registers</a>\n"
        "🔞 <a href='https://my.qbcc.qld.gov.au/myQBCC/s/excluded-individual-register'>Excluded Individuals (Banned)</a>\n"
        "📑 <a href='https://my.qbcc.qld.gov.au/myQBCC/s/adjudication-registry'>Adjudication Registry</a>\n"
        "📜 <a href='https://my.qbcc.qld.gov.au/myQBCC/s/building-certifier-licensee-register'>Building Certifiers</a>\n"
        "🏠 <a href='https://my.qbcc.qld.gov.au/myQBCC/s/owner-builder-licensee-register'>Owner Builders</a>"
    )

    send_telegram(header + body + footer)

if __name__ == "__main__":
    main()
