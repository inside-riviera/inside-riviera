import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

events = []

# --- 1. SCRAPE ITALIAN RIVIERA (rivieraeventi.it) ---
try:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    url_it = "https://www.rivieraeventi.it/it/eventi"
    res_it = requests.get(url_it, headers=headers, timeout=10)
    
    if res_it.status_code == 200:
        soup = BeautifulSoup(res_it.content, "html.parser")
        # Extract event elements
        cards = soup.select(".card-event, .event-item, article")
        
        for card in cards[:10]:
            title_el = card.select_one("h2, h3, .title")
            city_el = card.select_one(".location, .comune, .city")
            img_el = card.select_one("img")
            
            if title_el:
                title = title_el.get_text(strip=True)
                city = city_el.get_text(strip=True) if city_el else "Sanremo"
                img = img_el["src"] if img_el and "src" in img_el.attrs else "https://images.unsplash.com/photo-1507525428034-b723cf961d3e"
                
                # Default to today's date structure for newly scraped items
                now = datetime.now()
                events.append({
                    "id": len(events) + 1,
                    "year": now.year,
                    "month": now.month - 1, # JS 0-indexed month
                    "date": now.day,
                    "title": title,
                    "city": city,
                    "time": "See Details",
                    "tags": ["Market" if "mercato" in title.lower() else "Town Festival"],
                    "img": img,
                    "desc": f"Event in {city}: {title}. Check local announcements for exact schedule."
                })
except Exception as e:
    print(f"Error scraping Italian Riviera: {e}")

# --- 2. SCRAPE FRENCH RIVIERA (cotedazurfrance.com) ---
try:
    url_fr = "https://cotedazurfrance.com/discover/major-events/all-the-events-on-the-cote-dazur/"
    res_fr = requests.get(url_fr, headers=headers, timeout=10)
    
    if res_fr.status_code == 200:
        soup = BeautifulSoup(res_fr.content, "html.parser")
        cards = soup.select(".card, article, .event-card")
        
        for card in cards[:10]:
            title_el = card.select_one("h2, h3, .card-title")
            city_el = card.select_one(".location, .place")
            img_el = card.select_one("img")
            
            if title_el:
                title = title_el.get_text(strip=True)
                city = city_el.get_text(strip=True) if city_el else "Monte-Carlo"
                img = img_el["src"] if img_el and "src" in img_el.attrs else "https://images.unsplash.com/photo-1470225620780-dba8ba36b745"
                
                now = datetime.now()
                events.append({
                    "id": len(events) + 1,
                    "year": now.year,
                    "month": now.month - 1,
                    "date": now.day,
                    "title": title,
                    "city": city,
                    "time": "18:00",
                    "tags": ["Concert" if "music" in title.lower() else "Beach Party"],
                    "img": img,
                    "desc": f"French Riviera Event: {title} taking place in {city}."
                })
except Exception as e:
    print(f"Error scraping French Riviera: {e}")

# Save results to events.json
with open("events.json", "w", encoding="utf-8") as f:
    json.dump(events, f, ensure_ascii=False, indent=2)

print(f"Successfully saved {len(events)} events to events.json.")
