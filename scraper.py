import csv
import io
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import requests

# Live Published Google Sheet CSV URL
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

def extract_rss_image(item, description_text):
    # Check <enclosure> tags
    enclosure = item.find("enclosure")
    if enclosure is not None and "url" in enclosure.attrib:
        return enclosure.attrib["url"]
        
    # Check <media:content> or <media:thumbnail>
    for elem in item:
        if "content" in elem.tag or "thumbnail" in elem.tag:
            if "url" in elem.attrib:
                return elem.attrib["url"]
                
    # Extract <img> from HTML in description
    if description_text:
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', description_text)
        if img_match:
            return img_match.group(1)
            
    # Default fallback image
    return "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80"

# 1. READ CSV FROM GOOGLE SHEETS
try:
    response = requests.get(SHEET_CSV_URL, headers=headers, timeout=10)
    if response.status_code == 200:
        csv_data = csv.DictReader(io.StringIO(response.text))
        
        for row in csv_data:
            # Flexible column header checking
            city = row.get("Town") or row.get("town") or row.get("City") or "Riviera"
            feed_url = row.get("URL") or row.get("url") or row.get("Link")
            active = row.get("Active") or row.get("active") or "Yes"

            if active.strip().lower() == "yes" and feed_url and feed_url.startswith("http"):
                print(f"Scraping feed for {city}: {feed_url}")
                try:
                    feed_res = requests.get(feed_url, headers=headers, timeout=10)
                    if feed_res.status_code == 200:
                        root = ET.fromstring(feed_res.content)
                        items = root.findall(".//item")
                        
                        for idx, item in enumerate(items[:5]):
                            title_elem = item.find("title")
                            desc_elem = item.find("description")
                            link_elem = item.find("link")

                            if title_elem is not None and title_elem.text:
                                raw_title = title_elem.text
                                desc_raw = desc_elem.text if desc_elem is not None else ""
                                
                                title = clean_html(raw_title)[:70]
                                desc = clean_html(desc_raw)
                                event_url = link_elem.text.strip() if (link_elem is not None and link_elem.text) else feed_url
                                
                                # Spread dates slightly so calendar populates
                                event_date = today + timedelta(days=(idx % 5))

                                if len(title) > 5 and not any(k in title.lower() for k in ["privacy", "cookie", "policy"]):
                                    events.append({
                                        "id": len(events) + 1,
                                        "year": event_date.year,
                                        "month": event_date.month - 1,
                                        "date": event_date.day,
                                        "title": title,
                                        "city": city.strip(),
                                        "time": "18:00",
                                        "tags": [detect_tag(title)],
                                        "img": extract_rss_image(item, desc_raw),
                                        "desc": desc[:250] if desc else f"Official event scheduled in {city}.",
                                        "url": event_url
                                    })
                except Exception as e:
                    print(f"Error parsing feed for {city}: {e}")
    else:
        print(f"Failed to fetch Google Sheet. HTTP Status: {response.status_code}")

except Exception as e:
    print(f"Error connecting to Google Sheets CSV: {e}")

# 2. SAVE OUTPUT TO EVENTS.JSON
with open("events.json", "w", encoding="utf-8") as f:
    json.dump(events, f, ensure_ascii=False, indent=2)

print(f"Successfully processed and generated {len(events)} events in events.json")
