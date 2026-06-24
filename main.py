import os
from datetime import datetime

from fetch_news import load_sources, fetch_articles
from generate_script import generate_script
from generate_audio import generate_audio
from build_feed import add_episode, build_rss


def main():
    sources = load_sources()
    articles = fetch_articles(sources)

    if not articles:
        print("No relevant articles found today, skipping.")
        return

    today = datetime.utcnow().strftime("%Y-%m-%d")
    date_human = datetime.utcnow().strftime("%A, %B %d, %Y")
    result = generate_script(articles, date_human)
    episode_title = result["title"]
    script_text = result["script"]

    mp3_filename = f"episode-{today}.mp3"
    os.makedirs("docs", exist_ok=True)
    mp3_path = os.path.join("docs", mp3_filename)
    generate_audio(script_text, mp3_path)

    file_size = os.path.getsize(mp3_path)
    description = script_text[:300].rsplit(" ", 1)[0] + "..."

    episodes = add_episode(episode_title, description, mp3_filename, file_size)
    build_rss(episodes)

    print(f"Generated episode: {mp3_filename} -- \"{episode_title}\"")


if __name__ == "__main__":
    main()
