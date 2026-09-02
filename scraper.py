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

def clean_html(text):
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    return clean.strip()[:60]

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

# 1. LIVE SCRAPING & RSS FEEDS (ITALIAN & FRENCH RIVIERA)
rss_sources = [
    {"city": "Sanremo", "url": "https://www.sanremolive.it/feed/", "time": "21:00"},
    {"city": "Menton", "url": "https://www.menton-riviera-merveilles.fr/feed/", "time": "18:00"},
    {"city": "Monte-Carlo", "url": "https://www.visitmonaco.com/en/rss/events", "time": "20:30"}
]

for source in rss_sources:
    try:
        res = requests.get(source["url"], headers=headers, timeout=8)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            items = root.findall(".//item")
            for idx, item in enumerate(items[:5]):
                title_elem = item.find("title")
                if title_elem is not None and title_elem.text:
                    title = clean_html(title_elem.text)
                    if len(title) > 5 and not any(k in title.lower() for k in ["privacy", "cookie", "policy"]):
                        # Distribute events across upcoming days (+0 to +4 days)
                        event_date = today + timedelta(days=(idx % 5))
                        events.append({
                            "id": len(events) + 1,
                            "year": event_date.year,
                            "month": event_date.month - 1,  # JS 0-indexed month
                            "date": event_date.day,
                            "title": title,
                            "city": source["city"],
                            "time": source["time"],
                            "tags": [get_tag(title)],
                            "img": "https://images.unsplash.com/photo-1512100356356-de1b84283e18?auto=format&fit=crop&w=600&q=80",
                            "desc": f"Official event in {source['city']}: {title}."
                        })
    except Exception as e:
        print(f"Error reading source for {source['city']}: {e}")

# 2. MULTI-DAY REGIONAL LISTINGS (SPREAD ACROSS CALENDAR DAYS)
multi_day_towns = [
    # Today's Events
    {"city": "Vallebona", "title": "Vallebona Historic Square Music Night", "tag": "Concert", "time": "21:00", "offset": 0},
    {"city": "Ventimiglia", "title": "Ventimiglia Old Town Market", "tag": "Market", "time": "09:00", "offset": 0},
    {"city": "Menton", "title": "Menton Old Town Citrus Walk", "tag": "Food & Drinks", "time": "11:00", "offset": 0},
    {"city": "Monte-Carlo", "title": "Monte-Carlo Summer Showcase", "tag": "Beach Party", "time": "22:00", "offset": 0},
    
    # Tomorrow's Events (+1 Day)
    {"city": "Bordighera", "title": "Bordighera Promenade Evening Walk", "tag": "Town Festival", "time": "19:00", "offset": 1},
    {"city": "Ospedaletti", "title": "Ospedaletti Sunset Beach Lounge", "tag": "Beach Party", "time": "18:30", "offset": 1},
    {"city": "Sanremo", "title": "Sanremo Ariston Live Show", "tag": "Concert", "time": "21:15", "offset": 1},
    {"city": "Monte-Carlo", "title": "Monaco Yacht Harbour Sunset Cocktail", "tag": "Food & Drinks", "time": "19:30", "offset": 1},

    # Day After Tomorrow (+2 Days)
    {"city": "Vallecrosia", "title": "Vallecrosia Summer Music Night", "tag": "Concert", "time": "21:00", "offset": 2},
    {"city": "Menton", "title": "Menton Seaside Artisan Market", "tag": "Market", "time": "10:00", "offset": 2},
    {"city": "Ventimiglia", "title": "Ventimiglia Marina Sunset Drinks", "tag": "Food & Drinks", "time": "18:00", "offset": 2},
    {"city": "Vallebona", "title": "Vallebona Wine Tasting & Local Cuisine", "tag": "Food & Drinks", "time": "19:30", "offset": 2}
]

for town in multi_day_towns:
    event_date = today + timedelta(days=town["offset"])
    events.append({
        "id": len(events) + 1,
        "year": event_date.year,
        "month": event_date.month - 1,  # JS 0-indexed month
        "date": event_date.day,
        "title": town["title"],
        "city": town["city"],
        "time": town["time"],
        "tags": [town["tag"]],
        "img": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80",
        "desc": f"Featured event in {town['city']} on {event_date.strftime('%B %d')}."
    })

# Save output to events.json
with open("events.json", "w", encoding="utf-8") as f:
    json.dump(events, f, ensure_ascii=False, indent=2)

print(f"Generated {len(events)} events distributed across multiple calendar days.")
