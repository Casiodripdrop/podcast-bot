import feedparser
import json
from datetime import datetime, timedelta

KEYWORDS = [
    "deeptech", "deep tech", "robot", "robotics", "space", "satellite",
    "rocket", "spacetech", "space tech", "funding", "seed round",
    "series a", "series b", "series c", "raises", "raised", "startup",
]


def load_sources(path="feeds.json"):
    with open(path) as f:
        return json.load(f)["sources"]


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
