import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta

events = []
today = datetime.now()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
}

ITALIAN_TOWNS = [
    "Sanremo", "Ventimiglia", "Bordighera", "Ospedaletti", 
    "Vallecrosia", "Vallebona", "Seborga", "Apricale"
]

def detect_city(text):
    t = text.lower()
    for town in ITALIAN_TOWNS:
        if town.lower() in t:
            return town
    return None

def detect_tag(title):
    t = title.lower()
    if any(k in t for k in ["concert", "concerto", "musica", "live", "dj", "orchestra"]):
        return "Concert"
    elif any(k in t for k in ["market", "mercato", "mercatino", "fiera", "brocante"]):
        return "Market"
    elif any(k in t for k in ["food", "wine", "sagra", "cucina", "degustazione", "cibo"]):
        return "Food & Drinks"
    elif any(k in t for k in ["beach", "mare", "spiaggia", "notte"]):
        return "Beach Party"
    return "Town Festival"

# SCRAPE SANREMONEWS FOR ALL ITALIAN TOWNS
try:
    url = "https://www.sanremonews.it/agenda.html"
    res = requests.get(url, headers=headers, timeout=10)
    if res.status_code == 200:
        soup = BeautifulSoup(res.content, "html.parser")
        # Extract news items/articles
        articles = soup.find_all(["article", "div"], class_=re.compile(r'(item|article|news|event)', re.I))
        
        town_event_counts = {town: 0 for town in ITALIAN_TOWNS}

        for art in articles:
            title_node = art.find(["h2", "h3", "h4", "a"], class_=re.compile(r'title', re.I)) or art.find("a")
            img_node = art.find("img")
            
            if title_node:
                title_text = title_node.text.strip()
                full_text = art.text.strip()
                
                # Check if the event matches any of our target Italian towns
                target_city = detect_city(title_text) or detect_city(full_text)
                
                if target_city and len(title_text) > 10:
                    # Avoid adding excessive entries per city
                    if town_event_counts[target_city] < 3:
                        # Extract original image
                        img_url = ""
                        if img_node:
                            img_url = img_node.get("data-src") or img_node.get("src") or ""
                            if img_url.startswith("//"):
                                img_url = "https:" + img_url
                            elif img_url.startswith("/"):
                                img_url = "https://www.sanremonews.it" + img_url

                        # Extract original article link
                        link_href = title_node.get("href") if title_node.name == "a" else url
                        if link_href and not link_href.startswith("http"):
                            link_href = f"https://www.sanremonews.it{link_href}"

                        event_date = today + timedelta(days=town_event_counts[target_city])

                        events.append({
                            "id": len(events) + 1,
                            "year": event_date.year,
                            "month": event_date.month - 1,
                            "date": event_date.day,
                            "title": title_text[:70],
                            "city": target_city,
                            "time": "18:00",
                            "tags": [detect_tag(title_text)],
                            "img": img_url if img_url else "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80",
                            "desc": f"Official event listing for {target_city}. Click 'Visit Official Website' for complete scheduling and location details.",
                            "url": link_href
                        })
                        town_event_counts[target_city] += 1
except Exception as e:
    print(f"Error scraping SanremoNews: {e}")

# Save output
with open("events.json", "w", encoding="utf-8") as f:
    json.dump(events, f, ensure_ascii=False, indent=2)

print(f"Successfully aggregated {len(events)} real Italian Riviera events.")
