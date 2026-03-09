import os, requests, html
from bs4 import BeautifulSoup
from datetime import datetime

# === CONFIG ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Targeted QLD URLs
QLD_URLS = [
    "https://www.qbcc.qld.gov.au/news-resources/news",  # General News & Media Releases
    "https://www.qbcc.qld.gov.au/about-us/our-lists-registers" # Entry point for specific registers
]

def send_telegram(text):
    if not text: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=30)

def get_qld_data():
    print("🔍 Fetching QLD updates...")
    results = []
    seen_links = set()

    for url in QLD_URLS:
        try:
            r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
            soup = BeautifulSoup(r.content, "html.parser")
            
            # Target the news articles specifically
            content = soup.find('main') or soup.find('div', class_='views-element-container')
            if not content: continue

            for a in content.find_all('a', href=True):
                title = a.get_text().strip()
                link = a['href']
                
                # Cleanup Junk
                if len(title) < 15 or any(x in title.lower() for x in ["login", "facebook", "twitter", "top of page"]):
                    continue
                
                full_url = link if link.startswith("http") else f"https://www.qbcc.qld.gov.au{link}"
                
                if full_url not in seen_links:
                    label = "⚖️ REGISTER" if "register" in link or "list" in link else "📰 QLD NEWS"
                    results.append(f"• <b>[{label}]</b> {html.escape(title)}\n🔗 {full_url}")
                    seen_links.add(full_url)

        except Exception as e:
            print(f"Error: {e}")
            
    return results

def main():
    if not TELEGRAM_TOKEN or not CHAT_ID: return

    headlines = get_qld_data()
    header = f"☀️ <b>QBCC Queensland Update</b>\n📅 {datetime.now().strftime('%d %b %Y')}\n\n"
    
    body = "\n\n".join(headlines[:15]) if headlines else "<i>No new QLD headlines found.</i>"

    # Permanent QLD Resources
    footer = (
        "\n\n---\n"
        "<b>📂 QLD PERMANENT REGISTERS:</b>\n\n"
        "🚫 <b>Excluded Individuals (Banned):</b>\n"
        "https://www.qbcc.qld.gov.au/about-us/our-lists-registers/excluded-individuals-register\n\n"
        "📑 <b>Adjudication Decisions (Payment Disputes):</b>\n"
        "https://www.qbcc.qld.gov.au/about-us/our-lists-registers/adjudication-decision-register\n\n"
        "📉 <b>Suspended/Cancelled Licences:</b>\n"
        "https://www.qbcc.qld.gov.au/about-us/our-lists-registers/suspended-licences-register"
    )

    send_telegram(header + body + footer)

if __name__ == "__main__":
    main()
