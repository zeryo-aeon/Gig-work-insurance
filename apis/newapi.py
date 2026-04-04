import feedparser
import os
import re
import json
from groq import Groq
from dotenv import load_dotenv

# ==============================
# CONFIG
# ==============================

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=API_KEY)

DEBUG = True

FEEDS = [
    "https://indianexpress.com/section/india/feed/",
    "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    "https://timesofindia.indiatimes.com/rssfeeds/-2128833038.cms",
    "https://timesofindia.indiatimes.com/rssfeeds/-2128839596.cms",
    "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms",
    "https://www.thehindu.com/news/national/tamil-nadu/feeder/default.rss",
    "https://www.newindianexpress.com/states/tamil-nadu/rss",
    "https://www.thehindu.com/news/cities/chennai/feeder/default.rss",
    "https://indianexpress.com/section/cities/chennai/feed/",
    "https://mausam.imd.gov.in/rss/weather.xml",
]

STRONG_TRAFFIC = [
    "traffic", "accident", "crash", "collision",
    "jam", "congestion", "vehicle breakdown",
    "diversion", "road closed", "blocked",
    "lane closure", "signal failure"
]

EVENT_WORDS = [
    "procession", "rally", "protest", "march",
    "festival", "temple", "strike"
]

WEATHER_TRAFFIC = [
    "rain", "flood", "waterlogging", "heavy rain"
]

NEGATIVE_WORDS = [
    "gold", "price", "stock", "market",
    "exam", "result"
]

LOCATION_KEYWORDS = [
    "tamil nadu", "chennai", "coimbatore", "erode"
]

KNOWN_CITIES = [
    "chennai", "coimbatore", "erode", "salem",
    "madurai", "trichy", "tiruppur", "vellore"
]

MAX_RESULTS = 1000
MIN_GROQ_SCORE = 3


# ==============================
# DEBUG
# ==============================

def debug_print(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")


# ==============================
# CLEAN TEXT
# ==============================

def clean_text(text):
    try:
        return text.encode('latin1').decode('utf-8')
    except:
        return text


# ==============================
# FULL CONTENT EXTRACTION 🔥
# ==============================

def get_full_content(entry):
    parts = []

    if entry.get("title"):
        parts.append(entry["title"])

    if entry.get("summary"):
        parts.append(entry["summary"])

    if "content" in entry:
        try:
            for c in entry["content"]:
                parts.append(c.get("value", ""))
        except:
            pass

    return " ".join(parts)


# ==============================
# UTIL
# ==============================

def contains(text, words):
    text = text.lower()
    return any(w in text for w in words)


# ==============================
# LOCATION EXTRACTION 🔥
# ==============================

def extract_location(text):
    text_lower = text.lower()

    found_cities = []
    for city in KNOWN_CITIES:
        if city in text_lower:
            found_cities.append(city.title())

    matches = re.findall(r"(?:near|in|at|from|to)\s+([a-z\s]{3,40})", text_lower)

    areas = []
    for m in matches:
        cleaned = m.strip().title()
        if len(cleaned.split()) <= 4:
            areas.append(cleaned)

    return {
        "cities": list(set(found_cities)),
        "areas": list(set(areas[:5]))
    }


# ==============================
# ROUTE EXTRACTION
# ==============================

def extract_route_info(text):
    text_lower = text.lower()
    route = {}

    route_pattern = r"([a-z\s]+)[-–to]+([a-z\s]+)\s+(highway|road|expressway)"
    match = re.search(route_pattern, text_lower)

    if match:
        route["from"] = match.group(1).strip().title()
        route["to"] = match.group(2).strip().title()
        route["route_name"] = f"{route['from']} - {route['to']} {match.group(3).title()}"

    highway_pattern = r"\b(nh\s?\d+|national highway\s?\d+|sh\s?\d+)\b"
    hmatch = re.search(highway_pattern, text_lower)

    if hmatch:
        route["highway_number"] = hmatch.group(1).upper()

    near_pattern = r"(near|at|in)\s+([a-z\s]{3,30}?)(?:,|\.|$)"
    nmatch = re.search(near_pattern, text_lower)

    if nmatch:
        route["area"] = nmatch.group(2).strip().title()

    return route


# ==============================
# SCORE (USES FULL TEXT)
# ==============================

def calculate_score(full_text):
    content = full_text.lower()

    if contains(content, NEGATIVE_WORDS):
        return 0

    if not contains(content, LOCATION_KEYWORDS):
        return 0

    score = 1

    if contains(content, STRONG_TRAFFIC):
        score += 4

    if contains(content, EVENT_WORDS):
        score += 2

    if contains(content, WEATHER_TRAFFIC):
        score += 2

    return score


# ==============================
# GROQ
# ==============================

def groq_filter(news):
    prompt = f"""
You are a strict JSON generator.

Analyze the news and return ONLY a JSON object.
Do NOT return a list.

News:
{news.get("full_text", news["title"])}

Return:
{{
    "relevant": true or false,
    "type": "traffic" or "event" or "other",
    "severity": "low" or "medium" or "high",
    "from": "",
    "to": "",
    "road": "",
    "area": ""
}}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    return response.choices[0].message.content


# ==============================
# PARSE (ROBUST)
# ==============================

def parse_groq(text):
    try:
        json_part = text.split("```json")[-1].split("```")[0]
        data = json.loads(json_part)
    except:
        try:
            data = json.loads(text)
        except:
            return None

    if isinstance(data, list):
        return data[0] if data else None

    return data


def is_strictly_traffic(parsed):
    if not parsed or not isinstance(parsed, dict):
        return False

    if not parsed.get("relevant"):
        return False

    if parsed.get("type") not in ["traffic", "event"]:
        return False

    return True


# ==============================
# MERGE
# ==============================

def merge_route(route, ai):
    if not ai:
        return route

    if ai.get("area"):
        route["area"] = ai["area"]

    if ai.get("road"):
        route["route_name"] = ai["road"]

    if ai.get("from"):
        route["from"] = ai["from"]

    if ai.get("to"):
        route["to"] = ai["to"]

    return route


# ==============================
# FETCH
# ==============================

def fetch_news():
    seen = set()
    results = []

    for url in FEEDS:
        debug_print(f"Fetching: {url}")
        feed = feedparser.parse(url)

        for e in feed.entries:
            if e.link in seen:
                continue

            title = clean_text(e.title)
            summary = clean_text(e.get("summary", ""))

            raw_entry = {
                "title": title,
                "summary": summary,
                "content": e.get("content", [])
            }

            full_text = clean_text(get_full_content(raw_entry))

            score = calculate_score(full_text)

            if score >= MIN_GROQ_SCORE:
                results.append({
                    "title": title,
                    "summary": summary,
                    "full_text": full_text,
                    "link": e.link,
                    "score": score,
                    "location": extract_location(full_text),
                    "route": extract_route_info(full_text)
                })
                seen.add(e.link)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:20]


# ==============================
# PROCESS
# ==============================

def process(news_list):
    final = []

    for n in news_list:
        content = n.get("full_text", "").lower()

        if not (
            contains(content, STRONG_TRAFFIC) or
            contains(content, EVENT_WORDS) or
            contains(content, WEATHER_TRAFFIC)
        ):
            continue

        try:
            ai_raw = groq_filter(n)
            parsed = parse_groq(ai_raw)
        except:
            continue

        if is_strictly_traffic(parsed):
            n["route"] = merge_route(n["route"], parsed)
            n["ai"] = parsed
            final.append(n)

            if len(final) >= MAX_RESULTS:
                break

    return final


# ==============================
# DISPLAY
# ==============================

def display(news):
    if not news:
        print("❌ No traffic events found")
        return

    print("\n🚨 AI TRAFFIC INTELLIGENCE (FINAL)\n")
    print("=" * 80)

    for i, n in enumerate(news, 1):
        print(f"{i}. 📰 {n['title']}")
        print(f"   🔗 {n['link']}")
        print(f"   ⭐ Score: {n['score']}")

        print(f"   📍 Cities: {', '.join(n['location']['cities']) or 'N/A'}")
        print(f"   📍 Areas: {', '.join(n['location']['areas']) or 'N/A'}")

        r = n.get("route", {})
        print("   🧭 Route Info:")
        print(f"      From: {r.get('from', 'N/A')}")
        print(f"      To: {r.get('to', 'N/A')}")
        print(f"      Road: {r.get('route_name', r.get('highway_number', 'N/A'))}")
        print(f"      Area: {r.get('area', 'N/A')}")

        ai = n.get("ai", {})
        print(f"   🚨 Severity: {ai.get('severity', 'N/A')}")
        print(f"   🧠 Type: {ai.get('type', 'N/A')}\n")


# ==============================
# RUN
# ==============================

if __name__ == "__main__":
    raw = fetch_news()
    final = process(raw)
    display(final)