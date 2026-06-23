import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def generate_audio(script_text, output_path, voice="onyx"):
    """voice options: alloy, echo, fable, onyx, nova, shimmer"""
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=script_text,
    )
    response.stream_to_file(output_path)
