import os
from datetime import datetime

from fetch_news import (
    load_sources,
    fetch_articles,
    load_seen_links,
    save_seen_links,
    mark_as_seen,
)
from generate_script import generate_script, ScriptGenerationError
from generate_audio import generate_audio, tag_mp3
from generate_video import generate_video
from upload_youtube import upload_video
from build_feed import add_episode, build_rss, build_index_html

MIN_ARTICLES = 2


def main():
    sources = load_sources()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    seen = load_seen_links()
    all_fetched = fetch_articles(sources)
    articles = [a for a in all_fetched if a["link"] not in seen]

    print(f"Fetched {len(all_fetched)} candidate articles, "
          f"{len(articles)} are new (not covered in the last 14 days).")

    if len(articles) < MIN_ARTICLES:
        print(f"Only {len(articles)} new article(s) found (minimum is "
              f"{MIN_ARTICLES}) -- skipping today's episode.")
        return

    date_human = datetime.utcnow().strftime("%A, %B %d, %Y")
    try:
        result = generate_script(articles, date_human)
    except ScriptGenerationError:
        print("Script generation failed -- skipping today's episode.")
        return

    episode_title = result["title"]
    script_text = result["script"]

    # Audio
    mp3_filename = f"episode-{today}.mp3"
    os.makedirs("docs", exist_ok=True)
    mp3_path = os.path.join("docs", mp3_filename)
    generate_audio(script_text, mp3_path)
    tag_mp3(mp3_path, title=episode_title)

    # Podcast-Feed aktualisieren
    file_size = os.path.getsize(mp3_path)
    description = script_text[:300].rsplit(" ", 1)[0] + "..."
    episodes = add_episode(episode_title, description, mp3_filename, file_size)
    build_rss(episodes)
    build_index_html(episodes)

    # Video generieren
    video_path = "docs/latest_short.mp4"
    try:
        generate_video(mp3_path=mp3_path, title=episode_title, output_path=video_path)
    except Exception as e:
        print(f"Video-Generierung fehlgeschlagen (Podcast laeuft trotzdem): {e}")
        video_path = None

    # YouTube-Upload (nur wenn Video erfolgreich und Secrets vorhanden)
    if video_path and os.path.exists(video_path):
        if os.environ.get("YOUTUBE_REFRESH_TOKEN"):
            try:
                upload_video(
                    video_path=video_path,
                    title=episode_title,
                    description=description,
                    date_str=today,
                )
            except Exception as e:
                print(f"YouTube-Upload fehlgeschlagen (Podcast laeuft trotzdem): {e}")
        else:
            print("YOUTUBE_REFRESH_TOKEN nicht gesetzt, ueberspringe Upload.")

    # Gesehene Artikel speichern
    seen = mark_as_seen(all_fetched, seen, today)
    save_seen_links(seen)

    print(f"Generated episode: {mp3_filename} -- \"{episode_title}\"")


if __name__ == "__main__":
    main()
