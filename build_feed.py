import json
import os
from datetime import datetime, timezone
from email.utils import format_datetime

EPISODES_FILE = "docs/episodes.json"
FEED_FILE = "docs/feed.xml"
COVER_FILENAME = "cover.jpg"

# Wird per GitHub Actions Variable PODCAST_BASE_URL ueberschrieben.
# Format: https://<dein-github-username>.github.io/<repo-name>
BASE_URL = os.environ.get("PODCAST_BASE_URL", "https://YOURUSERNAME.github.io/podcast-bot")

# Spotify verlangt eine echte, im Feed sichtbare E-Mail-Adresse zur Verifizierung.
# Wird per Secret/Variable PODCAST_OWNER_EMAIL gesetzt.
OWNER_EMAIL = os.environ.get("PODCAST_OWNER_EMAIL", "you@example.com")
OWNER_NAME = os.environ.get("PODCAST_OWNER_NAME", "Deeptech Daily")


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
    new_entry = {
        "title": title,
        "description": description,
        "mp3_filename": mp3_filename,
        "file_size_bytes": file_size_bytes,
        "pub_date": pub_date,
        "duration": duration_seconds,
    }
    # Falls fuer diesen Dateinamen (= dasselbe Datum) schon ein Eintrag existiert,
    # ersetzen statt duplizieren (verhindert doppelte GUIDs im Feed).
    episodes = [ep for ep in episodes if ep["mp3_filename"] != mp3_filename]
    episodes.insert(0, new_entry)
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
      <link>{mp3_url}</link>
      <description>{_escape(ep['description'])}</description>
      <enclosure url="{mp3_url}" length="{ep['file_size_bytes']}" type="audio/mpeg" />
      <guid>{mp3_url}</guid>
      <pubDate>{ep['pub_date']}</pubDate>
      <itunes:duration>{ep['duration']}</itunes:duration>
      <itunes:image href="{BASE_URL}/{COVER_FILENAME}" />
      <itunes:explicit>false</itunes:explicit>
    </item>"""

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Deeptech Daily</title>
    <link>{BASE_URL}</link>
    <language>en-us</language>
    <description>A short daily briefing on deeptech, robotics, and space startups.</description>
    <itunes:author>{OWNER_NAME}</itunes:author>
    <itunes:explicit>false</itunes:explicit>
    <itunes:category text="Technology" />
    <itunes:image href="{BASE_URL}/{COVER_FILENAME}" />
    <image>
      <url>{BASE_URL}/{COVER_FILENAME}</url>
      <title>Deeptech Daily</title>
      <link>{BASE_URL}</link>
    </image>
    <itunes:owner>
      <itunes:name>{OWNER_NAME}</itunes:name>
      <itunes:email>{OWNER_EMAIL}</itunes:email>
    </itunes:owner>
    {items_xml}
  </channel>
</rss>"""

    os.makedirs(os.path.dirname(FEED_FILE), exist_ok=True)
    with open(FEED_FILE, "w") as f:
        f.write(rss)
