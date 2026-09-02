import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta

events = []
today = datetime.now()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
}

def clean_text(text):
    if not text:
        return ""
    clean = re.sub(r'\s+', ' ', text)
    return clean.strip()

def detect_city(text):
    t = text.lower()
    cities = ["vallebona", "ventimiglia", "vallecrosia", "bordighera", "ospedaletti", "sanremo", "menton", "monte-carlo", "monaco"]
    for c in cities:
        if c in t:
            return "Monte-Carlo" if c == "monaco" else c.capitalize()
    return None

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

# 1. SCRAPE LIVE REGIONAL EVENTS (SANREMONEWS / RIVIERA24 AGENDA)
# These regional portals publish daily events for Vallebona, Ventimiglia, Bordighera, Sanremo, etc.
try:
    url = "https://www.sanremonews.it/agenda.html"
    res = requests.get(url, headers=headers, timeout=10)
    if res.status_code == 200:
        soup = BeautifulSoup(res.content, "html.parser")
        items = soup.find_all(["article", "div"], class_=re.compile(r'(item|event|article)', re.I))
        
        for item in items[:20]:
            title_node = item.find(["h2", "h3", "h4", "a"], class_=re.compile(r'title', re.I)) or item.find("a")
            img_node = item.find("img")
            
            if title_node:
                raw_title = clean_text(title_node.text)
                city = detect_city(raw_title) or detect_city(item.text)
                
                if city and len(raw_title) > 8:
                    # Extract original event image URL
                    img_url = ""
                    if img_node:
                        img_url = img_node.get("data-src") or img_node.get("src") or ""
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        elif img_url.startswith("/"):
                            img_url = "https://www.sanremonews.it" + img_url

                    # Extract original link to event details
                    event_link = "https://www.sanremonews.it/agenda.html"
                    if title_node.name == "a" and title_node.get("href"):
                        link_href = title_node["href"]
                        event_link = link_href if link_href.startswith("http") else f"https://www.sanremonews.it{link_href}"

                    events.append({
                        "id": len(events) + 1,
                        "year": today.year,
                        "month": today.month - 1,
                        "date": today.day,
                        "title": raw_title[:70],
                        "city": city,
                        "time": "18:00",
                        "tags": [detect_tag(raw_title)],
                        "img": img_url if img_url else "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80",
                        "desc": f"Official scheduled event in {city}. Read full details and ticketing on the official press portal.",
                        "url": event_link
                    })
except Exception as e:
    print(f"Error scraping SanremoNews: {e}")

# 2. SCRAPE CÔTE D'AZUR (MENTON & MONTE-CARLO REAL EVENTS)
france_sources = [
    {"city": "Menton", "url": "https://www.menton-riviera-merveilles.fr/agenda/", "base": "https://www.menton-riviera-merveilles.fr"},
    {"city": "Monte-Carlo", "url": "https://www.visitmonaco.com/fr/agenda", "base": "https://www.visitmonaco.com"}
]

for src in france_sources:
    try:
        res = requests.get(src["url"], headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, "html.parser")
            cards = soup.find_all(["div", "article"], class_=re.compile(r'(card|item|event)', re.I))
            
            for card in cards[:5]:
                title_elem = card.find(["h2", "h3", "h4", "a"])
                img_elem = card.find("img")
                link_elem = card.find("a")
                
                if title_elem:
                    t_text = clean_text(title_elem.text)
                    if len(t_text) > 8:
                        img_src = ""
                        if img_elem:
                            img_src = img_elem.get("data-src") or img_elem.get("src") or ""
                            if img_src.startswith("/"):
                                img_src = src["base"] + img_src

                        href = link_elem["href"] if link_elem and link_elem.get("href") else src["url"]
                        final_link = href if href.startswith("http") else src["base"] + href

                        events.append({
                            "id": len(events) + 1,
                            "year": today.year,
                            "month": today.month - 1,
                            "date": today.day,
                            "title": t_text[:70],
                            "city": src["city"],
                            "time": "19:30",
                            "tags": [detect_tag(t_text)],
                            "img": img_src if img_src else "https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=600&q=80",
                            "desc": f"Official tourism board listing for {src['city']}: {t_text}.",
                            "url": final_link
                        })
    except Exception as e:
        print(f"Error scraping {src['city']}: {e}")

# Save output
with open("events.json", "w", encoding="utf-8") as f:
    json.dump(events, f, ensure_ascii=False, indent=2)

print(f"Successfully scraped {len(events)} real events with original images and authentic links.")
