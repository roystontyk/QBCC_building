import os, requests, html
from bs4 import BeautifulSoup
from datetime import datetime

# === CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# The specific QBCC news landing page
QLD_URLS = [
    "https://www.qbcc.qld.gov.au/news-resources/news"
]

def send_telegram(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=30)
    print(f"Telegram response: {r.status_code}")

def get_qld_data():
    print("🔍 Fetching QLD updates for March 2026...")
    results = []
    seen_links = set()

    for url in QLD_URLS:
        try:
            r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
            soup = BeautifulSoup(r.content, "html.parser")
            
            # 2026 QBCC Structure: News items are usually in .views-row or article tags
            articles = soup.select('.views-row, article, .news-item')
            
            for item in articles:
                link_tag = item.find('a', href=True)
                if not link_tag: continue
                
                title = link_tag.get_text().strip()
                link = link_tag['href']
                
                # Cleanup: Skip short text or common nav items
                if len(title) < 10 or any(x in title.lower() for x in ["read more", "view all", "contact us"]):
                    continue
                
                full_url = link if link.startswith("http") else f"https://www.qbcc.qld.gov.au{link}"
                
                if full_url not in seen_links:
                    # Identify the type (Article, Media Release, etc.)
                    tag = "📰 QLD NEWS"
                    if "media-release" in full_url: tag = "📢 MEDIA"
                    elif "public-warning" in full_url: tag = "⚠️ WARNING"
                    
                    results.append(f"• <b>[{tag}]</b> {html.escape(title)}\n🔗 {full_url}")
                    seen_links.add(full_url)

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            
    return results

def main():
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Error: Missing Telegram Environment Variables!")
        return

    headlines = get_qld_data()
    print(f"Found {len(headlines)} headlines.")

    header = f"☀️ <b>QBCC Queensland Update</b>\n📅 {datetime.now().strftime('%d %b %Y')}\n\n"
    
    if headlines:
        body = "\n\n".join(headlines[:15])
    else:
        body = "<i>No new QLD headlines found. Check the direct links below.</i>"

    footer = (
        "\n\n---\n"
        "<b>📂 QLD PERMANENT REGISTERS:</b>\n\n"
        "🚫 <b>Excluded Individuals (Banned):</b>\n"
        "https://www.qbcc.qld.gov.au/about-us/our-lists-registers/excluded-individuals-register\n\n"
        "📑 <b>Adjudication Decisions:</b>\n"
        "https://www.qbcc.qld.gov.au/about-us/our-lists-registers/adjudication-decision-register"
    )

    send_telegram(header + body + footer)

if __name__ == "__main__":
    main()
