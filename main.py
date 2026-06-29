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
from build_feed import add_episode, build_rss, build_index_html

# Unter dieser Anzahl neuer Artikel wird der Tag ausgelassen, statt eine
# erzwungene Episode ohne echte Substanz zu erzeugen. Dank mehr Quellen und
# der Anti-Erfindungs-Regel im Prompt reicht ein niedriger Wert hier aus.
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
              f"{MIN_ARTICLES}) -- skipping today's episode rather than "
              f"forcing a thin one.")
        return

    date_human = datetime.utcnow().strftime("%A, %B %d, %Y")
    try:
        result = generate_script(articles, date_human)
    except ScriptGenerationError:
        print("Script generation failed (invalid response from Claude) -- "
              "skipping today's episode rather than publishing broken content.")
        return

    episode_title = result["title"]
    script_text = result["script"]

    mp3_filename = f"episode-{today}.mp3"
    os.makedirs("docs", exist_ok=True)
    mp3_path = os.path.join("docs", mp3_filename)
    generate_audio(script_text, mp3_path)
    tag_mp3(mp3_path, title=episode_title)

    file_size = os.path.getsize(mp3_path)
    description = script_text[:300].rsplit(" ", 1)[0] + "..."

    episodes = add_episode(episode_title, description, mp3_filename, file_size)
    build_rss(episodes)
    build_index_html(episodes)

    # Alle heute betrachteten Artikel als "gesehen" markieren (auch die, die
    # Claude am Ende nicht ins Skript aufgenommen hat -- sonst koennten sie
    # morgen erneut auftauchen, obwohl sie schon "alte" News sind).
    seen = mark_as_seen(all_fetched, seen, today)
    save_seen_links(seen)

    print(f"Generated episode: {mp3_filename} -- \"{episode_title}\"")


if __name__ == "__main__":
    main()
