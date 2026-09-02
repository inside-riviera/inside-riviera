import requests
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime, timedelta

events = []
today = datetime.now()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
}

IMAGE_BANK = {
    "Market": "https://images.unsplash.com/photo-1488459716781-31db52582fe9?auto=format&fit=crop&w=600&q=80",
    "Concert": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=600&q=80",
    "Food & Drinks": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=600&q=80",
    "Beach Party": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80",
    "Town Festival": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80",
    "Monte-Carlo": "https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=600&q=80",
    "Menton": "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=600&q=80"
}

def extract_rss_image(item, description_text):
    enclosure = item.find("enclosure")
    if enclosure is not None and "url" in enclosure.attrib:
        return enclosure.attrib["url"]
    for elem in item:
        if "content" in elem.tag or "thumbnail" in elem.tag:
            if "url" in elem.attrib:
                return elem.attrib["url"]
    if description_text:
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', description_text)
        if img_match:
            return img_match.group(1)
    return None

def clean_html(text):
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()

def get_tag(title):
    t = title.lower()
    if any(k in t for k in ["concert", "concerto", "musica", "music"]):
        return "Concert"
    elif any(k in t for k in ["market", "mercato", "mercatino"]):
        return "Market"
    elif any(k in t for k in ["food", "drinks", "sagra", "cucina", "degustazione"]):
        return "Food & Drinks"
    elif any(k in t for k in ["beach", "party", "festa", "notte"]):
        return "Beach Party"
    return "Town Festival"

# 1. LIVE RSS SCRAPING WITH URL LINKS
rss_sources = [
    {"city": "Sanremo", "url": "https://www.sanremolive.it/feed/", "time": "21:00", "base_site": "https://www.sanremolive.it"},
    {"city": "Menton", "url": "https://www.menton-riviera-merveilles.fr/feed/", "time": "18:00", "base_site": "https://www.menton-riviera-merveilles.fr"},
    {"city": "Monte-Carlo", "url": "https://www.visitmonaco.com/en/rss/events", "time": "20:30", "base_site": "https://www.visitmonaco.com"}
]

for source in rss_sources:
    try:
        res = requests.get(source["url"], headers=headers, timeout=8)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            items = root.findall(".//item")
            for idx, item in enumerate(items[:5]):
                title_elem = item.find("title")
                desc_elem = item.find("description")
                link_elem = item.find("link")
                
                desc_raw = desc_elem.text if desc_elem is not None else ""
                event_url = link_elem.text if link_elem is not None and link_elem.text else source["base_site"]
                
                if title_elem is not None and title_elem.text:
                    title = clean_html(title_elem.text)[:60]
                    clean_desc = clean_html(desc_raw)
                    if not clean_desc or len(clean_desc) < 10:
                        clean_desc = f"Join us in {source['city']} for {title}. Visit the official website for additional venue and ticket details."
                    else:
                        clean_desc = clean_desc[:250] + "..."

                    if len(title) > 5 and not any(k in title.lower() for k in ["privacy", "cookie", "policy"]):
                        event_date = today + timedelta(days=(idx % 5))
                        tag = get_tag(title)
                        extracted_img = extract_rss_image(item, desc_raw)
                        final_img = extracted_img if extracted_img else IMAGE_BANK.get(source["city"], IMAGE_BANK[tag])

                        events.append({
                            "id": len(events) + 1,
                            "year": event_date.year,
                            "month": event_date.month - 1,
                            "date": event_date.day,
                            "title": title,
                            "city": source["city"],
                            "time": source["time"],
                            "tags": [tag],
                            "img": final_img,
                            "desc": clean_desc,
                            "url": event_url
                        })
    except Exception as e:
        print(f"RSS extraction error for {source['city']}: {e}")

# 2. MULTI-DAY REGIONAL LISTINGS WITH LINKS
multi_day_towns = [
    {
        "city": "Vallebona", "title": "Vallebona Village Walk & Wine Tasting", "tag": "Food & Drinks", "time": "18:00", "offset": 0,
        "img": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=600&q=80",
        "desc": "Explore the narrow alleys of historic Vallebona followed by local Rossese wine tasting and authentic Ligurian appetizers.",
        "url": "https://www.vallebona.info"
    },
    {
        "city": "Ventimiglia", "title": "Ventimiglia Old Town Artisan Market", "tag": "Market", "time": "09:30", "offset": 0,
        "img": "https://images.unsplash.com/photo-1533900298318-6b8da08a523e?auto=format&fit=crop&w=600&q=80",
        "desc": "Discover handcrafted items, fresh local produce, and regional specialties along the picturesque streets of Ventimiglia Alta.",
        "url": "https://www.comune.ventimiglia.im.it"
    },
    {
        "city": "Bordighera", "title": "Bordighera Lungomare Evening Walk", "tag": "Town Festival", "time": "19:00", "offset": 1,
        "img": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80",
        "desc": "An evening stroll along Argentina Promenade featuring live acoustic music, local food pop-ups, and beachside crafts.",
        "url": "https://www.bordighera.it"
    },
    {
        "city": "Ospedaletti", "title": "Ospedaletti Sunset Beach Lounge", "tag": "Beach Party", "time": "18:30", "offset": 1,
        "img": "https://images.unsplash.com/photo-1519046904884-53103b34b206?auto=format&fit=crop&w=600&q=80",
        "desc": "Relax by the shore with chilled music, aperitivo, and panoramic sunset views over the Gulf of Ospedaletti.",
        "url": "https://www.comune.ospedaletti.im.it"
    },
    {
        "city": "Vallecrosia", "title": "Vallecrosia Summer Concert Night", "tag": "Concert", "time": "21:00", "offset": 2,
        "img": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=600&q=80",
        "desc": "Live open-air performance featuring local Riviera bands and classical performances under the stars.",
        "url": "https://www.comune.vallecrosia.im.it"
    },
    {
        "city": "Monte-Carlo", "title": "Monaco Yacht Harbour Sunset Cocktail", "tag": "Food & Drinks", "time": "19:30", "offset": 1,
        "img": "https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=600&q=80",
        "desc": "Exclusive seaside lounge event overlooking Port Hercule with signature drinks and live ambient DJ sets.",
        "url": "https://www.visitmonaco.com"
    }
]

for item in multi_day_towns:
    event_date = today + timedelta(days=item["offset"])
    events.append({
        "id": len(events) + 1,
        "year": event_date.year,
        "month": event_date.month - 1,
        "date": event_date.day,
        "title": item["title"],
        "city": item["city"],
        "time": item["time"],
        "tags": [item["tag"]],
        "img": item["img"],
        "desc": item["desc"],
        "url": item["url"]
    })

with open("events.json", "w", encoding="utf-8") as f:
    json.dump(events, f, ensure_ascii=False, indent=2)

print(f"Generated {len(events)} events complete with descriptions and external links.")
