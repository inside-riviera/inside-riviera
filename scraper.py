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

def clean_html(text):
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()

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

# Read Google Sheet Configuration
try:
    response = requests.get(SHEET_CSV_URL, headers=headers, timeout=10)
    if response.status_code == 200:
        csv_data = csv.DictReader(io.StringIO(response.text))
        
        for row in csv_data:
            city = (row.get("Town") or row.get("town") or row.get("City") or "Riviera").strip()
            feed_url = (row.get("URL") or row.get("url") or row.get("Link") or "").strip()
            active = (row.get("Active") or row.get("active") or "Yes").strip()

            if active.lower() == "yes" and feed_url.startswith("http"):
                print(f"Processing source for {city}: {feed_url}")
                try:
                    res = requests.get(feed_url, headers=headers, timeout=10)
                    if res.status_code == 200:
                        
                        # 1. SANREMONEWS HTML PARSING (ITALIAN TOWNS)
                        if "sanremonews.it" in feed_url:
                            soup = BeautifulSoup(res.content, "html.parser")
                            articles = soup.find_all(["article", "div"], class_=re.compile(r'(item|article|news|event)', re.I))
                            
                            found = 0
                            for art in articles:
                                title_node = art.find(["h2", "h3", "h4", "a"], class_=re.compile(r'title', re.I)) or art.find("a")
                                img_node = art.find("img")
                                
                                if title_node:
                                    t_text = clean_html(title_node.text)
                                    full_text = clean_html(art.text)
                                    
                                    # Match articles containing the specific town name
                                    if city.lower() in full_text.lower() and len(t_text) > 10:
                                        img_url = ""
                                        if img_node:
                                            img_url = img_node.get("data-src") or img_node.get("src") or ""
                                            if img_url.startswith("//"):
                                                img_url = "https:" + img_url
                                            elif img_url.startswith("/"):
                                                img_url = "https://www.sanremonews.it" + img_url

                                        link_href = title_node.get("href") if title_node.name == "a" else feed_url
                                        if link_href and not link_href.startswith("http"):
                                            link_href = f"https://www.sanremonews.it{link_href}"

                                        event_date = today + timedelta(days=found)

                                        events.append({
                                            "id": len(events) + 1,
                                            "year": event_date.year,
                                            "month": event_date.month - 1,
                                            "date": event_date.day,
                                            "title": t_text[:70],
                                            "city": city,
                                            "time": "18:00",
                                            "tags": [detect_tag(t_text)],
                                            "img": img_url if img_url else "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80",
                                            "desc": f"Official scheduled event in {city}. Click below to read the full report on SanremoNews.",
                                            "url": link_href
                                        })
                                        found += 1
                                        if found >= 3:
                                            break

                        # 2. STANDARD RSS XML PARSING (MENTON & MONTE-CARLO)
                        else:
                            try:
                                root = ET.fromstring(res.content)
                                items = root.findall(".//item")
                                for idx, item in enumerate(items[:3]):
                                    title_elem = item.find("title")
                                    desc_elem = item.find("description")
                                    link_elem = item.find("link")

                                    if title_elem is not None and title_elem.text:
                                        t_clean = clean_html(title_elem.text)[:70]
                                        desc_clean = clean_html(desc_elem.text if desc_elem is not None else "")
                                        e_url = link_elem.text.strip() if (link_elem is not None and link_elem.text) else feed_url
                                        event_date = today + timedelta(days=idx)

                                        events.append({
                                            "id": len(events) + 1,
                                            "year": event_date.year,
                                            "month": event_date.month - 1,
                                            "date": event_date.day,
                                            "title": t_clean,
                                            "city": city,
                                            "time": "19:00",
                                            "tags": [detect_tag(t_clean)],
                                            "img": "https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=600&q=80",
                                            "desc": desc_clean[:250] if desc_clean else f"Official event in {city}.",
                                            "url": e_url
                                        })
                            except Exception as xml_err:
                                print(f"XML parse error for {city}: {xml_err}")

                except Exception as e:
                    print(f"Error requesting feed for {city}: {e}")

except Exception as e:
    print(f"Error fetching Google Sheet CSV: {e}")

# Save JSON file
with open("events.json", "w", encoding="utf-8") as f:
    json.dump(events, f, ensure_ascii=False, indent=2)

print(f"Successfully processed {len(events)} events into events.json")
