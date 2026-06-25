import feedparser
import json
import os
from datetime import datetime, timedelta

KEYWORDS = [
    "deeptech", "deep tech", "robot", "robotics", "space", "satellite",
    "rocket", "spacetech", "space tech", "funding", "seed round",
    "series a", "series b", "series c", "raises", "raised", "startup",
]

SEEN_FILE = "docs/seen_links.json"
SEEN_MAX_AGE_DAYS = 14  # aeltere Eintraege verfallen, damit die Datei nicht unbegrenzt waechst


def load_sources(path="feeds.json"):
    with open(path) as f:
        return json.load(f)["sources"]


def load_seen_links(path=SEEN_FILE, max_age_days=SEEN_MAX_AGE_DAYS):
    """Laedt bereits verwendete Artikel-Links der letzten N Tage: {link: 'YYYY-MM-DD'}"""
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        seen = json.load(f)
    cutoff = datetime.utcnow().date() - timedelta(days=max_age_days)
    fresh = {}
    for link, date_str in seen.items():
        try:
            if datetime.strptime(date_str, "%Y-%m-%d").date() >= cutoff:
                fresh[link] = date_str
        except ValueError:
            continue
    return fresh


def save_seen_links(seen, path=SEEN_FILE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(seen, f, indent=2)


def mark_as_seen(articles, seen, today_str=None):
    """Markiert alle heute gefundenen Artikel als 'gesehen', damit sie an \
    Folgetagen nicht erneut auftauchen -- unabhaengig davon, ob Claude sie \
    am Ende tatsaechlich ins Skript aufgenommen hat."""
    today_str = today_str or datetime.utcnow().strftime("%Y-%m-%d")
    for a in articles:
        seen[a["link"]] = today_str
    return seen


def fetch_articles(sources, hours_back=36, max_per_feed=10):
    """Pull entries from each RSS feed, filter by keyword + recency, dedupe by link."""
    cutoff = datetime.utcnow() - timedelta(hours=hours_back)
    articles = []
    seen_links = set()

    for source in sources:
        try:
            feed = feedparser.parse(source["url"])
        except Exception as e:
            print(f"Failed to parse {source['url']}: {e}")
            continue

        count = 0
        for entry in feed.entries:
            if count >= max_per_feed:
                break

            link = entry.get("link", "")
            if not link or link in seen_links:
                continue

            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            text_blob = (title + " " + summary).lower()
            if not any(kw in text_blob for kw in KEYWORDS):
                continue

            published = entry.get("published_parsed") or entry.get("updated_parsed")
            if published:
                pub_dt = datetime(*published[:6])
                if pub_dt < cutoff:
                    continue

            articles.append({
                "source": source["name"],
                "title": title,
                "summary": summary,
                "link": link,
            })
            seen_links.add(link)
            count += 1

    return articles


if __name__ == "__main__":
    srcs = load_sources()
    arts = fetch_articles(srcs)
    print(f"Found {len(arts)} relevant articles")
    for a in arts:
        print(f"- [{a['source']}] {a['title']}")
