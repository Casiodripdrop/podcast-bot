import json
import os
from datetime import datetime, timezone
from email.utils import format_datetime

EPISODES_FILE = "docs/episodes.json"
FEED_FILE = "docs/feed.xml"
# Wird per GitHub Actions Variable PODCAST_BASE_URL ueberschrieben.
# Format: https://<dein-github-username>.github.io/<repo-name>
BASE_URL = os.environ.get("PODCAST_BASE_URL", "https://YOURUSERNAME.github.io/podcast-bot")


def load_episodes():
    if os.path.exists(EPISODES_FILE):
        with open(EPISODES_FILE) as f:
            return json.load(f)
    return []


def save_episodes(episodes):
    with open(EPISODES_FILE, "w") as f:
        json.dump(episodes, f, indent=2)


def add_episode(title, description, mp3_filename, file_size_bytes, duration_seconds=300):
    episodes = load_episodes()
    pub_date = format_datetime(datetime.now(timezone.utc))
    episodes.insert(0, {
        "title": title,
        "description": description,
        "mp3_filename": mp3_filename,
        "file_size_bytes": file_size_bytes,
        "pub_date": pub_date,
        "duration": duration_seconds,
    })
    save_episodes(episodes)
    return episodes


def _escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_rss(episodes):
    items_xml = ""
    for ep in episodes:
        mp3_url = f"{BASE_URL}/{ep['mp3_filename']}"
        items_xml += f"""
    <item>
      <title>{_escape(ep['title'])}</title>
      <description>{_escape(ep['description'])}</description>
      <enclosure url="{mp3_url}" length="{ep['file_size_bytes']}" type="audio/mpeg" />
      <guid>{mp3_url}</guid>
      <pubDate>{ep['pub_date']}</pubDate>
      <itunes:duration>{ep['duration']}</itunes:duration>
    </item>"""

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Deeptech Daily</title>
    <link>{BASE_URL}</link>
    <language>en-us</language>
    <description>A short daily briefing on deeptech, robotics, and space startups.</description>
    <itunes:author>Deeptech Daily</itunes:author>
    <itunes:explicit>false</itunes:explicit>
    <itunes:category text="Technology" />
    {items_xml}
  </channel>
</rss>"""

    os.makedirs(os.path.dirname(FEED_FILE), exist_ok=True)
    with open(FEED_FILE, "w") as f:
        f.write(rss)
