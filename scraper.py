from bs4 import BeautifulSoup
import json
import requests

urls = [
    "https://www.sanremoliveandlove.it/eventi/",
    "https://www.visitbordighera.it/eventi",
    "https://ventimiglia.it/eventi-manifestazioni/",
    "https://www.visitospedaletti.it/eventi/",
    "https://turismo.comune.vallecrosia.im.it/eventi-e-notizie/",
    "https://www.vallebona.info/it/calendario-eventi",
    "https://www.sanremonews.it/agenda.html",
]

headers = {"User-Agent": "Mozilla/5.0"}
events = []

for url in urls:
  try:
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
      soup = BeautifulSoup(response.text, "html.parser")
      # Example placeholder logic:
      # Find event containers on the page and extract data into the `events` list
  except Exception as e:
    print(f"Error scraping {url}: {e}")

with open("events.json", "w", encoding="utf-8") as f:
  json.dump(events, f, indent=2, ensure_ascii=False)
