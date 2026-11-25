#!/usr/bin/env python3
"""Generate crawlable, individual pages for upcoming events in the public Inside Riviera SheetDB."""
import datetime as dt
import hashlib
import html
import json
import os
import re
from urllib.parse import quote
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
API = "https://sheetdb.io/api/v1/nxxtx0pb2uuw7"
SHEET_NAME = os.environ.get("SHEETDB_SHEET", "events").strip()
API_URL = API + ("?sheet=" + quote(SHEET_NAME) if SHEET_NAME else "")
BASE = "https://www.insideriviera.net"
MANIFEST = ROOT / "event-pages-manifest.json"
SITEMAP = ROOT / "sitemap.xml"

def norm(row):
    return {re.sub(r"[\s_-]", "", str(k)).lower(): v for k, v in row.items()}

def get(row, *keys):
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""

def date_part(value):
    try:
        n = int(float(str(value).replace(",", "").strip()))
        return n
    except (TypeError, ValueError):
        return None

def safe_http(value):
    from urllib.parse import urlparse
    p = urlparse(value)
    return value if p.scheme in ("http", "https") and p.netloc else ""

def slugify(value):
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:65].strip("-") or "riviera-event"

def json_script(value):
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")

def page_for(event, canonical):
    title = html.escape(event["title"])
    city = html.escape(event["city"])
    venue = html.escape(event["venue"])
    description = html.escape(event["description"])
    date_label = event["start"].strftime("%A, %-d %B %Y")
    meta = event["description"] or f"{event['title']} in {event['city']}."
    meta = html.escape(meta[:155])
    official = event["official"]
    image = event["image"]
    event_time = html.escape(event["time"])
    category = html.escape(event["category"])
    place = {"@type": "Place", "name": event["venue"] or event["city"]}
    if event["city"]:
        place["address"] = {"@type": "PostalAddress", "addressLocality": event["city"]}
    schema = {
        "@context": "https://schema.org", "@type": "Event",
        "name": event["title"], "startDate": event["start"].isoformat(),
        "location": place, "url": canonical
    }
    if event["end"]:
        schema["endDate"] = event["end"].isoformat()
    if image:
        schema["image"] = [image]
    if event["description"]:
        schema["description"] = event["description"]
    img_html = f'<img class="event-image" src="{html.escape(image, quote=True)}" alt="{title}" loading="lazy">' if image else ""
    official_html = f'<p><a class="button" href="{html.escape(official, quote=True)}" rel="noopener noreferrer">Check the organiser’s event information ↗</a></p>' if official else ""
    venue_line = f'<p class="meta">📍 {venue + " · " if venue else ""}{city}</p>' if city or venue else ""
    time_line = f'<p class="meta">🕒 {event_time}</p>' if event_time else ""
    category_line = f'<p class="meta">Event type: {category}</p>' if category else ""
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} in {city} | Inside Riviera</title>
<meta name="description" content="{meta}">
<link rel="canonical" href="{canonical}"><meta name="robots" content="index,follow">
<meta property="og:type" content="event"><meta property="og:site_name" content="Inside Riviera">
<meta property="og:title" content="{title} in {city}"><meta property="og:description" content="{meta}">
<meta property="og:url" content="{canonical}">
{f'<meta property="og:image" content="{html.escape(image, quote=True)}">' if image else ''}
<script id="Cookiebot" src="https://consent.cookiebot.com/uc.js" data-cbid="ea71097e-77cf-48d5-b2ec-c10ddde7a251" data-blockingmode="auto" type="text/javascript"></script>
<link rel="icon" href="/favicon.png"><link rel="stylesheet" href="/inside-riviera-design.css">
<script type="application/ld+json">{json_script(schema)}</script>
<style>
:root{{--navy:#0f1c36;--pink:#ff007a;--lime:#a3e635}}*{{box-sizing:border-box}}
body{{margin:0;background:#f6f8fb;color:var(--navy);font:16px/1.7 system-ui,Arial,sans-serif}}
header,footer{{background:var(--navy);color:white;padding:20px max(20px,calc((100vw - 900px)/2))}}
header a,footer a{{color:white}}main{{max-width:900px;margin:35px auto;padding:0 20px}}
article{{background:white;border:1px solid #e4e9f0;border-radius:18px;padding:clamp(22px,5vw,42px)}}
h1{{font-size:clamp(32px,6vw,52px);line-height:1.12;margin:10px 0}}
.meta{{color:#52617a}}.event-image{{width:100%;max-height:420px;object-fit:cover;border-radius:12px}}
.button{{display:inline-block;background:var(--pink);color:white;padding:12px 18px;border-radius:9px;text-decoration:none;font-weight:800}}
.note{{font-size:14px;color:#61708a}}.back{{color:#b9005e}}
</style></head><body>
<header><a href="/">INSIDE RIVIERA</a></header><main>
<a class="back" href="/events-riviera.html">← Explore Riviera events</a>
<article>{img_html}<p class="meta">📅 {html.escape(date_label)}</p>{venue_line}{time_line}{category_line}
<h1>{title}</h1>
{f'<p>{description}</p>' if description else '<p>For the latest programme, timing and access information, check the organiser’s event information before travelling.</p>'}
{official_html}
<p class="note">Event information can change. Confirm dates, times, prices and availability with the organiser before setting out. Inside Riviera is an independent events guide.</p>
</article></main><footer><a href="/">Home</a> · <a href="/about.html">About</a> · <a href="/contact.html">Contact</a></footer>
</body></html>"""

def main():
    req = urllib.request.Request(API_URL, headers={"User-Agent": "InsideRivieraEventPublisher/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        rows = json.loads(response.read().decode("utf-8"))
    if not isinstance(rows, list):
        raise RuntimeError("SheetDB did not return an event list.")
    if not rows:
        raise RuntimeError("SheetDB returned zero rows. No pages or sitemap entries were changed; check the selected worksheet tab and API permissions.")

    today = dt.date.today()
    generated = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        row = norm(raw)
        title = get(row, "title", "titolo", "name", "event")
        city = get(row, "city", "citta", "town", "location")
        if not title or not city:
            continue
        year = date_part(get(row, "startyear", "year", "anno", "yr"))
        month = date_part(get(row, "startmonth", "month", "mese", "mo"))
        day = date_part(get(row, "startdate", "day", "giorno", "data"))
        if not (year and month and day):
            continue
        try:
            start = dt.date(year, month, day)
        except ValueError:
            continue
        end = None
        ey = date_part(get(row, "endyear", "endanno"))
        em = date_part(get(row, "endmonth", "endmese"))
        ed = date_part(get(row, "enddate", "endgiorno"))
        if ey and em and ed:
            try:
                end = dt.date(ey, em, ed)
            except ValueError:
                pass
        if (end or start) < today:
            continue
        description = get(row, "description", "desc", "descrizione", "details", "info")
        official = safe_http(get(row, "link", "url", "website", "sito", "ticketlink"))
        venue = get(row, "venue", "location", "luogo", "address", "place")
        image = safe_http(get(row, "img", "image", "photo", "picture", "foto", "imgurl", "imageurl"))
        event_time = get(row, "time", "orario", "hours", "ora")
        category = get(row, "category", "categoria", "type", "tipo")
        # Keep thin spreadsheet entries out of Google’s index. A page needs a substantial
        # event-specific description plus at least two useful supporting details.
        supporting_details = [official, venue, event_time, category, image]
        if len(description) < 180 or sum(bool(value) for value in supporting_details) < 2:
            continue
        identity = "|".join([title.lower(), city.lower(), start.isoformat()])
        suffix = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:7]
        slug = f"{slugify(title)}-{slugify(city)}-{start.isoformat()}-{suffix}"
        filename = f"event-{slug}.html"
        canonical = f"{BASE}/{filename}"
        event = {"title": title, "city": city, "venue": venue, "description": description,
                 "official": official, "image": image, "time": event_time, "category": category,
                 "start": start, "end": end}
        (ROOT / filename).write_text(page_for(event, canonical), encoding="utf-8")
        generated.append(filename)

    old = []
    if MANIFEST.exists():
        try:
            old = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            old = []
    for filename in old:
        if filename not in generated and re.fullmatch(r"event-[a-z0-9-]+\.html", str(filename)):
            (ROOT / filename).unlink(missing_ok=True)
    MANIFEST.write_text(json.dumps(sorted(generated), indent=2) + "\n", encoding="utf-8")

    if SITEMAP.exists():
        tree = ET.parse(SITEMAP)
        root = tree.getroot()
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        existing = {el.text for el in root.findall("sm:url/sm:loc", ns)}
        for filename in generated:
            url = f"{BASE}/{filename}"
            if url not in existing:
                node = ET.SubElement(root, "{http://www.sitemaps.org/schemas/sitemap/0.9}url")
                ET.SubElement(node, "{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text = url
                ET.SubElement(node, "{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod").text = today.isoformat()
        for node in list(root.findall("sm:url", ns)):
            loc = node.find("sm:loc", ns)
            if loc is not None and loc.text and re.fullmatch(re.escape(BASE) + r"/event-[a-z0-9-]+\.html", loc.text):
                if loc.text.rsplit("/", 1)[-1] not in generated:
                    root.remove(node)
        tree.write(SITEMAP, encoding="utf-8", xml_declaration=True)
    print(f"Generated {len(generated)} upcoming event pages.")
if __name__ == "__main__":
    main()
