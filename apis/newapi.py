import feedparser
import os
import re
import json
from groq import Groq
from dotenv import load_dotenv

try:
    from utils.logger import app_logger
except ImportError:
    import logging
    app_logger = logging.getLogger("NewsWrapper")

class NewsWrapper:
    # Traffic & Filtering Constants
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

    def __init__(self, api_key: str = None, debug: bool = True):
        """Initialize News Wrapper with Groq API key and settings."""
        load_dotenv()
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.api_key)
        self.debug = debug
        self.max_results = 20
        self.min_groq_score = 3

    def debug_print(self, msg: str):
        app_logger.debug(f"NEWS: {msg}")

    def clean_text(self, text: str) -> str:
        try:
            return text.encode('latin1').decode('utf-8')
        except:
            return text

    def get_full_content(self, entry: dict) -> str:
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

    def contains_any(self, text: str, words: list) -> bool:
        text = text.lower()
        return any(w in text for w in words)

    def extract_location(self, text: str) -> dict:
        text_lower = text.lower()
        found_cities = [city.title() for city in self.KNOWN_CITIES if city in text_lower]
        
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

    def extract_route_info(self, text: str) -> dict:
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

    def calculate_score(self, full_text: str) -> int:
        content = full_text.lower()
        if self.contains_any(content, self.NEGATIVE_WORDS) or not self.contains_any(content, self.LOCATION_KEYWORDS):
            return 0

        score = 1
        if self.contains_any(content, self.STRONG_TRAFFIC): score += 4
        if self.contains_any(content, self.EVENT_WORDS): score += 2
        if self.contains_any(content, self.WEATHER_TRAFFIC): score += 2
        return score

    def groq_filter(self, news: dict) -> str:
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
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return response.choices[0].message.content

    def parse_groq(self, text: str) -> dict:
        try:
            json_part = text.split("```json")[-1].split("```")[0]
            data = json.loads(json_part)
        except:
            try:
                data = json.loads(text)
            except:
                return None
        return data[0] if isinstance(data, list) and data else data

    def is_strictly_traffic(self, parsed: dict) -> bool:
        if not parsed or not isinstance(parsed, dict): return False
        return parsed.get("relevant") and parsed.get("type") in ["traffic", "event"]

    def merge_route(self, route: dict, ai: dict) -> dict:
        if not ai: return route
        for key in ["area", "from", "to"]:
            if ai.get(key): route[key] = ai[key]
        if ai.get("road"): route["route_name"] = ai["road"]
        return route

    def fetch_news(self) -> list:
        seen = set()
        results = []

        for url in self.FEEDS:
            self.debug_print(f"Fetching: {url}")
            feed = feedparser.parse(url)

            for e in feed.entries:
                if e.link in seen: continue

                title = self.clean_text(e.title)
                summary = self.clean_text(e.get("summary", ""))
                raw_entry = {"title": title, "summary": summary, "content": e.get("content", [])}
                full_text = self.clean_text(self.get_full_content(raw_entry))
                score = self.calculate_score(full_text)

                if score >= self.min_groq_score:
                    results.append({
                        "title": title,
                        "summary": summary,
                        "full_text": full_text,
                        "link": e.link,
                        "score": score,
                        "location": self.extract_location(full_text),
                        "route": self.extract_route_info(full_text)
                    })
                    seen.add(e.link)

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:20]

    def process(self, news_list: list) -> list:
        final = []
        for n in news_list:
            content = n.get("full_text", "").lower()
            if not (self.contains_any(content, self.STRONG_TRAFFIC) or 
                    self.contains_any(content, self.EVENT_WORDS) or 
                    self.contains_any(content, self.WEATHER_TRAFFIC)):
                continue

            try:
                ai_raw = self.groq_filter(n)
                parsed = self.parse_groq(ai_raw)
            except:
                continue

            if self.is_strictly_traffic(parsed):
                n["route"] = self.merge_route(n["route"], parsed)
                n["ai"] = parsed
                final.append(n)
                if len(final) >= self.max_results: break
        return final

    def display(self, news: list):
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

if __name__ == "__main__":
    wrapper = NewsWrapper()
    raw = wrapper.fetch_news()
    final = wrapper.process(raw)
    wrapper.display(final)