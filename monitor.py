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
    requests.post(url, json={
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "HTML", 
        "disable_web_page_preview": True
    }, timeout=30)

def get_qld_data():
    print("🔍 Fetching QBCC Headlines (Stealth Mode)...")
    results = []
    seen_links = set()
    
    # --- STEALTH LOGIC START ---
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })
    # --- STEALTH LOGIC END ---

    try:
        # Initial request to establish session/cookies
        session.get("https://www.qbcc.qld.gov.au/", timeout=15)
        
        # Actual page fetch
        r = session.get(QLD_URL, timeout=20)
        print(f"Response Status: {r.status_code}")
        
        soup = BeautifulSoup(r.content, "html.parser")
        
        # Target individual news rows/articles
        articles = soup.select('.views-row, article, .news-item')
        
        for item in articles:
            # isolate the heading tag specifically to exclude teaser text
            heading_tag = item.find(['h3', 'h2', 'h4'])
            link_tag = item.find('a', href=True)
            
            if not heading_tag or not link_tag:
                continue
            
            # Clean up the heading text
            raw_title = heading_tag.get_text().strip()
            # Regex to remove "Article |", "Media Release |", dates, and "Read More"
            clean_title = re.sub(r'(Article|News|Campaign|Media release|Read More|\| \d+ \w+ \d{4})', '', raw_title, flags=re.IGNORECASE).strip()
            
            # Re-verify we didn't just grab an empty string or nav link
            if len(clean_title) < 10:
                continue
                
            link = link_tag['href']
            full_url = link if link.startswith("http") else f"https://www.qbcc.qld.gov.au{link}"
            
            if full_url not in seen_links:
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
        body = "\n\n".join(headlines[:15]) # Increased to 15 items
    else:
        body = "<i>No new QLD headings found today (Check Stealth/Session settings).</i>"

    footer = (
        "\n\n---\n"
        "<b>📂 QLD PERMANENT REGISTERS:</b>\n"
        "🟡 <a href='https://my.qbcc.qld.gov.au/myQBCC/s/suspended-registers'>Suspended Registers</a>\n"
        "🔴 <a href='https://my.qbcc.qld.gov.au/myQBCC/s/cancelled-registers'>Cancelled Registers</a>\n"
        "🚫 <a href='https://my.qbcc.qld.gov.au/myQBCC/s/excluded-individual-register'>Excluded Individuals (Banned)</a>\n"
        "📑 <a href='https://my.qbcc.qld.gov.au/myQBCC/s/adjudication-registry'>Adjudication Registry</a>\n"
        "📜 <a href='https://my.qbcc.qld.gov.au/myQBCC/s/building-certifier-licensee-register'>Building Certifiers</a>\n"
        "🏠 <a href='https://my.qbcc.qld.gov.au/myQBCC/s/owner-builder-licensee-register'>Owner Builders</a>"
    )

    send_telegram(header + body + footer)

if __name__ == "__main__":
    main()
