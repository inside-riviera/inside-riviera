import requests
import json
from datetime import datetime, timedelta

events = []
today = datetime.now()

# Event templates for each city
city_events = [
    # Vallebona
    {"city": "Vallebona", "title": "Vallebona Village Walk & Wine Tasting", "time": "18:00", "tag": "Food & Drinks"},
    {"city": "Vallebona", "title": "Acoustic Guitar in Old Town Square", "time": "21:00", "tag": "Concert"},
    # Ventimiglia
    {"city": "Ventimiglia", "title": "Ventimiglia Waterfront Promenade Market", "time": "09:30", "tag": "Market"},
    {"city": "Ventimiglia", "title": "Sunset Cocktails at the New Marina", "time": "19:00", "tag": "Food & Drinks"},
    # Vallecrosia
    {"city": "Vallecrosia", "title": "Vallecrosia Open Air Cinema & Music", "time": "21:00", "tag": "Town Festival"},
    # Bordighera
    {"city": "Bordighera", "title": "Bordighera Lungomare Evening Crafts Stalls", "time": "19:30", "tag": "Market"},
    {"city": "Bordighera", "title": "Seaside DJ Set & Aperitivo", "time": "18:30", "tag": "Beach Party"},
    # Ospedaletti
    {"city": "Ospedaletti", "title": "Ospedaletti Sunset Lounge Session", "time": "18:00", "tag": "Beach Party"},
    # Sanremo
    {"city": "Sanremo", "title": "Sanremo Symphony Orchestra Night", "time": "21:15", "tag": "Concert"},
    # Menton (Côte d'Azur)
    {"city": "Menton", "title": "Menton Old Town Citrus & Local Market Tour", "time": "10:30", "tag": "Market"},
    {"city": "Menton", "title": "Menton Promenade Live Jazz Evening", "time": "20:30", "tag": "Concert"},
    # Monte-Carlo (Monaco)
    {"city": "Monte-Carlo", "title": "Monte-Carlo Beach Club Sunset Party", "time": "19:00", "tag": "Beach Party"},
    {"city": "Monte-Carlo", "title": "Monaco Harbor Open Air Light & Music Show", "time": "22:00", "tag": "Town Festival"}
]

# Spread events dynamically across the next 7 days
event_id = 1
for day_offset in range(7):
    target_date = today + timedelta(days=day_offset)
    
    # Select 3-4 distinct towns for each day
    daily_selection = city_events[(day_offset * 2): (day_offset * 2) + 4]
    
    for item in daily_selection:
        events.append({
            "id": event_id,
            "year": target_date.year,
            "month": target_date.month - 1,  # 0-indexed for JS
            "date": target_date.day,
            "title": item["title"],
            "city": item["city"],
            "time": item["time"],
            "tags": [item["tag"]],
            "img": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80",
            "desc": f"Featured event in {item['city']} on {target_date.strftime('%A, %B %d')}."
        })
        event_id += 1

with open("events.json", "w", encoding="utf-8") as f:
    json.dump(events, f, ensure_ascii=False, indent=2)

print(f"Generated {len(events)} events spanning from day {today.day} to {today.day + 6}.")
