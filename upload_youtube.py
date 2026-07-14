"""
upload_youtube.py
Laedt das generierte Short-Video auf YouTube hoch.
Nutzt OAuth2 Refresh Token aus Umgebungsvariablen (GitHub Secrets).
"""

import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def get_youtube_client():
    """Erstellt einen authentifizierten YouTube API-Client aus den Secrets."""
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)


def upload_video(video_path: str, title: str, description: str, date_str: str):
    """
    Laedt ein Video als YouTube Short hoch.
    - Titel: Episodentitel (max 100 Zeichen)
    - Description: kurze Beschreibung + Feed-Link
    - Tags: deeptech, robotics, space, startups, podcast
    """
    youtube = get_youtube_client()

    full_title = title[:97] + "..." if len(title) > 100 else title
    full_description = (
        f"{description}\n\n"
        f"📻 Vollständige Episode: https://casiodripdrop.github.io/podcast-bot/\n"
        f"🎙️ Täglich neues Deeptech-Briefing über Robotics, Space & Startups.\n\n"
        f"#DeeptechDaily #Deeptech #Robotics #Space #Startups #Podcast #TechNews"
    )

    body = {
        "snippet": {
            "title": full_title,
            "description": full_description,
            "tags": [
                "deeptech", "robotics", "space", "startups", "podcast",
                "tech news", "AI", "spacetech", "VC", "funding"
            ],
            "categoryId": "28",  # Science & Technology
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=5 * 1024 * 1024,  # 5MB Chunks
    )

    print(f"Lade hoch: {title}")
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"Video erfolgreich hochgeladen: https://youtube.com/watch?v={video_id}")
    return video_id


if __name__ == "__main__":
    # Lokaler Test (braucht Secrets als Env-Variablen)
    upload_video(
        video_path="docs/test_short.mp4",
        title="SpaceX Secret Mission + $200M for Agility Robotics",
        description="Today's top stories in deeptech, robotics, and space startups.",
        date_str="2026-06-24",
    )
