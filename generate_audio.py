import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

MAX_CHARS = 3900  # etwas Puffer unter dem 4096-Zeichen-Limit von OpenAI TTS

# "nova" wirkt energetischer/heller als "onyx" (ruhig/tief).
# speed: 0.25-4.0, 1.0 = normal. Per Variable TTS_SPEED ueberschreibbar.
DEFAULT_VOICE = os.environ.get("TTS_VOICE", "nova")
DEFAULT_SPEED = float(os.environ.get("TTS_SPEED", "1.15"))


def split_text(text, max_len=MAX_CHARS):
    """Teilt den Text an Satzenden in Stuecke <= max_len Zeichen auf."""
    sentences = text.replace("\n", " ").split(". ")
    chunks = []
    current = ""
    for s in sentences:
        piece = s if s.endswith((".", "!", "?")) else s + "."
        candidate = (current + " " + piece).strip() if current else piece
        if len(candidate) > max_len and current:
            chunks.append(current.strip())
            current = piece
        else:
            current = candidate
    if current:
        chunks.append(current.strip())
    return chunks


def generate_audio(script_text, output_path, voice=None, speed=None):
    """voice options: alloy, echo, fable, onyx, nova, shimmer"""
    voice = voice or DEFAULT_VOICE
    speed = speed if speed is not None else DEFAULT_SPEED
    chunks = split_text(script_text)
    with open(output_path, "wb") as out_f:
        for chunk in chunks:
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=chunk,
                speed=speed,
            )
            out_f.write(response.content)
