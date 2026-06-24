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
      <link>{BASE_URL}</link>
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
    <itunes:type>episodic</itunes:type>
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


def _format_display_date(pub_date_rfc822):
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(pub_date_rfc822)
        return dt.strftime("%B %d, %Y")
    except Exception:
        return pub_date_rfc822


def build_index_html(episodes):
    """Baut eine einfache Landingpage, damit der <link>-Tag im Feed auf eine echte
    Webseite zeigt (sonst meckern Validatoren/Player ueber "failed to load website")."""
    episode_blocks = ""
    for ep in episodes[:30]:  # nur die letzten 30 anzeigen, Seite bleibt schlank
        mp3_url = f"{BASE_URL}/{ep['mp3_filename']}"
        display_date = _format_display_date(ep["pub_date"])
        episode_blocks += f"""
    <article class="episode">
      <h2>{_escape(ep['title'])}</h2>
      <p class="date">{display_date}</p>
      <audio controls preload="none" src="{mp3_url}"></audio>
      <p class="desc">{_escape(ep['description'])}</p>
    </article>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Deeptech Daily</title>
<style>
  body {{
    background: #121110;
    color: #f0ebe4;
    font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    max-width: 720px;
    margin: 0 auto;
    padding: 40px 20px 80px;
  }}
  header {{ text-align: center; margin-bottom: 50px; }}
  header img {{ width: 160px; height: 160px; border-radius: 12px; border: 2px solid #c45a29; }}
  h1 {{ font-size: 28px; letter-spacing: 1px; margin: 20px 0 6px; }}
  .tagline {{ color: #c45a29; letter-spacing: 2px; font-size: 13px; text-transform: uppercase; }}
  .subscribe {{ margin-top: 18px; font-size: 14px; color: #999; word-break: break-all; }}
  .episode {{
    border-top: 1px solid #2a2826;
    padding: 26px 0;
  }}
  .episode h2 {{ font-size: 18px; margin: 0 0 6px; }}
  .episode .date {{ color: #777; font-size: 13px; margin: 0 0 14px; }}
  .episode audio {{ width: 100%; margin-bottom: 14px; }}
  .episode .desc {{ color: #c9c4bc; font-size: 14px; line-height: 1.5; }}
</style>
</head>
<body>
  <header>
    <img src="{COVER_FILENAME}" alt="Deeptech Daily cover art" />
    <h1>DEEPTECH DAILY</h1>
    <div class="tagline">Robotics · Space · Startups</div>
    <p class="subscribe">RSS-Feed zum Abonnieren: {BASE_URL}/feed.xml</p>
  </header>
  {episode_blocks}
</body>
</html>"""

    index_path = os.path.join(os.path.dirname(FEED_FILE), "index.html")
    with open(index_path, "w") as f:
        f.write(html)
