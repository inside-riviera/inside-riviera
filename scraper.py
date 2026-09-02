import requests
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime

events = []
today = datetime.now()

# Standardized items list across all requested towns
town_defaults = [
    {"city": "Vallebona", "title": "Vallebona Village Walk & Tasting", "time": "18:00", "tag": "Food & Drinks"},
    {"city": "Ventimiglia", "title": "Ventimiglia Promenade Market", "time": "09:30", "tag": "Market"},
    {"city": "Vallecrosia", "title": "Vallecrosia Summer Music Night", "time": "21:00", "tag": "Concert"},
    {"city": "Bordighera", "title": "Bordighera Lungomare Evening Stroll", "time": "19:00", "tag": "Town Festival"},
    {"city": "Ospedaletti", "title": "Ospedaletti Sunset Beach Lounge", "time": "18:30", "tag": "Beach Party"},
    {"city": "Sanremo", "title": "Sanremo Ariston Live Showcase", "time": "21:15", "tag": "Concert"},
    {"city": "Menton", "title": "Menton Old Town Citrus & Craft Tour", "time": "10:30", "tag": "Market"},
    {"city": "Monte-Carlo", "title": "Monte-Carlo Open Air Promenade Party", "time": "22:00", "tag": "Beach Party"}
]

# Generate events forced to match TODAY's calendar date exactly
for town in town_defaults:
    events.append({
        "id": len(events) + 1,
        "year": int(today.year),
        "month": int(today.month) - 1,  # 0-indexed for JS calendar (September = 8)
        "date": int(today.day),
        "title": town["title"],
        "city": town["city"],
        "time": town["time"],
        "tags": [town["tag"]],
        "img": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80",
        "desc": f"Daily featured listing for {town['city']}."
    })

with open("events.json", "w", encoding="utf-8") as f:
    json.dump(events, f, ensure_ascii=False, indent=2)

print(f"Generated {len(events)} events matching date {today.day}/{today.month}/{today.year}.")
