"""
generate_video.py
Erstellt ein ~60-Sekunden-Audiogram-Video aus der Episode-MP3:
- Dunkler Hintergrund im //ZWEIG-Stil (burnt orange + fast-schwarz)
- Cover-Art zentriert
- Episodentitel als animierter Text
- Waveform-Animation (FFmpeg showwaves)
- "Deeptech Daily" Branding
Output: docs/latest_short.mp4 (wird taeglich ueberschrieben)
"""

import os
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont

BG_COLOR = (18, 16, 15)
ACCENT = (196, 90, 41)
TEXT_COLOR = (240, 235, 228)
WIDTH = 1080
HEIGHT = 1920  # Shorts-Format (9:16)
DURATION = 59  # Sekunden (unter 60s = YouTube Shorts)

COVER_PATH = "docs/cover.jpg"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_PATH_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def build_background_frame(title: str, output_path: str):
    """Erstellt ein statisches PNG als Hintergrund fuer das Video."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Horizontale Akzentlinie oben
    draw.rectangle([0, 0, WIDTH, 8], fill=ACCENT)

    # Branding oben
    try:
        brand_font = ImageFont.truetype(FONT_PATH, 42)
        sub_font = ImageFont.truetype(FONT_PATH_REG, 32)
        title_font = ImageFont.truetype(FONT_PATH, 52)
    except Exception:
        brand_font = sub_font = title_font = ImageFont.load_default()

    brand_text = "DEEPTECH DAILY"
    bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
    bw = bbox[2] - bbox[0]
    draw.text(((WIDTH - bw) / 2, 60), brand_text, font=brand_font, fill=ACCENT)

    sub_text = "ROBOTICS · SPACE · STARTUPS"
    bbox = draw.textbbox((0, 0), sub_text, font=sub_font)
    sw = bbox[2] - bbox[0]
    draw.text(((WIDTH - sw) / 2, 120), sub_text, font=sub_font, fill=TEXT_COLOR)

    # Cover-Art zentriert einfuegen
    try:
        cover = Image.open(COVER_PATH).convert("RGB")
        cover = cover.resize((700, 700))
        cover_x = (WIDTH - 700) // 2
        cover_y = 220
        img.paste(cover, (cover_x, cover_y))
        # Rahmen um Cover
        draw.rectangle(
            [cover_x - 3, cover_y - 3, cover_x + 703, cover_y + 703],
            outline=ACCENT,
            width=3,
        )
    except Exception as e:
        print(f"Cover-Art konnte nicht geladen werden: {e}")
        cover_y = 220

    # Waveform-Platzhalter (wird von FFmpeg ueberschrieben)
    wave_y = 1050
    draw.rectangle([80, wave_y, WIDTH - 80, wave_y + 160], fill=(30, 28, 27))

    # Episodentitel (mehrzeilig, zentriert)
    title_y = 1260
    wrapped = textwrap.wrap(title, width=28)
    for i, line in enumerate(wrapped[:3]):  # max 3 Zeilen
        bbox = draw.textbbox((0, 0), line, font=title_font)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        draw.text(((WIDTH - lw) / 2, title_y + i * (lh + 16)),
                  line, font=title_font, fill=TEXT_COLOR)

    # Horizontale Akzentlinie unten
    draw.rectangle([0, HEIGHT - 8, WIDTH, HEIGHT], fill=ACCENT)

    img.save(output_path, quality=95)
    print(f"Hintergrund-Frame erstellt: {output_path}")


def generate_video(mp3_path: str, title: str, output_path: str):
    """Kombiniert Hintergrund-Frame + MP3-Waveform per FFmpeg zu einem Video."""
    bg_path = "/tmp/deeptech_bg.png"
    build_background_frame(title, bg_path)

    # Waveform-Region definieren (Y-Position im Bild)
    wave_y = 1050
    wave_h = 160

    # FFmpeg-Kommando:
    # 1. Standbild als Endlosschleife
    # 2. Audio aus MP3 (auf DURATION Sekunden begrenzt)
    # 3. showwaves-Filter fuer die Waveform-Animation
    # 4. Overlay der Waveform auf das Standbild
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", bg_path,
        "-i", mp3_path,
        "-filter_complex",
        (
            f"[1:a]showwaves=s={WIDTH - 160}x{wave_h}:"
            f"mode=cline:colors=C45A29|C45A29:scale=sqrt[wave];"
            f"[0:v][wave]overlay=80:{wave_y}[v]"
        ),
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-t", str(DURATION),
        "-pix_fmt", "yuv420p",
        "-r", "30",
        output_path,
    ]

    print("Generiere Video...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg Fehler:", result.stderr[-1000:])
        raise RuntimeError("Video-Generierung fehlgeschlagen")
    print(f"Video erstellt: {output_path}")


if __name__ == "__main__":
    # Lokaler Test
    generate_video(
        mp3_path="docs/episode-2026-06-24.mp3",
        title="SpaceX Secret Mission + $200M for Agility Robotics",
        output_path="docs/test_short.mp4",
    )
