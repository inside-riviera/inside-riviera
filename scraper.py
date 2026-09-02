import csv
import io
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRQ4moUdcf26QzV-0IvLLyp3VP88TsdDrrrnyH-ZznZXRwXVoUw4GE3jd1qKtWCllqEzK3onHvX1GTR/pub?gid=0&single=true&output=csv"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
}

events = []
today = datetime.now()

# Positive keywords required to count as a valid event
EVENT_KEYWORDS = [
    "concert", "concerto", "musica", "fest", "sagra", "mercato", "mercatino", 
    "fiera", "mostra", "spettacolo", "teatro", "degustazione", "notte", 
    "tour", "visita", "cinema", "dj", "live", "dance", "festa", "brocante"
]

# Negative keywords to strictly reject civic/administrative notices
EXCLUDE_KEYWORDS = [
    "quanto sono chiare", "informazioni su questa pagina", "bando", "contributi", 
    "asili nido", "truffa", "caldo intenso", "acqua", "polizia", "consiglio comunale", 
    "delibera", "orario", "uffici", "servizio", "avviso", "privacy", "cookie", 
    "anagrafe", "scuola", "elettorale", "esplora tutte", "pagopa", "spid"
]

def clean_html(text):
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()

def is_valid_event(title):
    t = title.lower()
    # Reject administrative fluff
    if any(neg in t for neg in EXCLUDE_KEYWORDS):
        return False
    # Accept if matches known event keywords or is a valid press title from RSS
    return any(pos in t for pos in EVENT_KEYWORDS) or len(t) > 15

def detect_tag(title):
    t = title.lower()
    if any(k in t for k in ["concert", "concerto", "musica", "orchestra", "live", "dj"]):
        return "Concert"
    elif any(k in t for k in ["market", "mercato", "mercatino", "fiera", "brocante"]):
        return "Market"
    elif any(k in t for k in ["food", "wine", "sagra", "cucina", "degustazione", "aperitivo"]):
        return "Food & Drinks"
    elif any(k in t for k in ["beach", "mare", "spiaggia", "notte", "party"]):
        return "Beach Party"
    return "Town Festival"

# Read CSV Sheet
try:
    response = requests.get(SHEET_CSV_URL, headers=headers, timeout=10)
    if response.status_code == 200:
        csv_data = csv.DictReader(io.StringIO(response.text))
        
        for row in csv_data:
            city = row.get("Town") or row.get("town") or row.get("City") or "Riviera"
            feed_url = row.get("URL") or row.get("url") or row.get("Link")
            active = row.get("Active") or row.get("active") or "Yes"

            if active.strip().lower() == "yes" and feed_url and feed_url.startswith("http"):
                print(f"Scraping source for {city}: {feed_url}")
                try:
                    feed_res = requests.get(feed_url, headers=headers, timeout=10)
                    if feed_res.status_code == 200:
                        parsed_rss = False
                        
                        # 1. Parse RSS XML
                        try:
                            root = ET.fromstring(feed_res.content)
                            items = root.findall(".//item")
                            if items:
                                parsed_rss = True
                                count = 0
                                for item in items:
                                    title_elem = item.find("title")
                                    desc_elem = item.find("description")
                                    link_elem = item.find("link")

                                    if title_elem is not None and title_elem.text:
                                        title = clean_html(title_elem.text)[:70]
                                        if is_valid_event(title):
                                            desc = clean_html(desc_elem.text if desc_elem is not None else "")
                                            event_url = link_elem.text.strip() if (link_elem is not None and link_elem.text) else feed_url
                                            event_date = today + timedelta(days=count)

                                            events.append({
                                                "id": len(events) + 1,
                                                "year": event_date.year,
                                                "month": event_date.month - 1,
                                                "date": event_date.day,
                                                "title": title,
                                                "city": city.strip(),
                                                "time": "18:00",
                                                "tags": [detect_tag(title)],
                                                "img": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80",
                                                "desc": desc[:250] if desc else f"Scheduled event in {city}.",
                                                "url": event_url
                                            })
                                            count += 1
                                            if count >= 3:
                                                break
                        except Exception:
                            parsed_rss = False

                        # 2. Parse HTML directly (if not RSS)
                        if not parsed_rss:
                            soup = BeautifulSoup(feed_res.content, "html.parser")
                            tags = soup.find_all(["h2", "h3", "h4", "a"], class_=re.compile(r'(title|event|news|article|titolo)', re.I))
                            
                            count = 0
                            for tag_elem in tags:
                                text_clean = clean_html(tag_elem.text)
                                if is_valid_event(text_clean):
                                    event_date = today + timedelta(days=count)
                                    link_href = tag_elem.get("href") if tag_elem.name == "a" else feed_url
                                    if link_href and not link_href.startswith("http"):
                                        link_href = feed_url

                                    events.append({
                                        "id": len(events) + 1,
                                        "year": event_date.year,
                                        "month": event_date.month - 1,
                                        "date": event_date.day,
                                        "title": text_clean[:70],
                                        "city": city.strip(),
                                        "time": "18:00",
                                        "tags": [detect_tag(text_clean)],
                                        "img": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80",
                                        "desc": f"Official municipal event in {city}.",
                                        "url": link_href or feed_url
                                    })
                                    count += 1
                                    if count >= 3:
                                        break
                except Exception as e:
                    print(f"Error reading source for {city}: {e}")

except Exception as e:
    print(f"Error fetching CSV: {e}")

# Save output
with open("events.json", "w", encoding="utf-8") as f:
    json.dump(events, f, ensure_ascii=False, indent=2)

print(f"Successfully filtered and saved {len(events)} valid events.")
