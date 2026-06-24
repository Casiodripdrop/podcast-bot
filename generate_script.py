import os
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

PROMPT_TEMPLATE = """You are the host of a short daily podcast called "Deeptech Daily" \
covering deeptech, robotics, and space startups.

Below are recent articles. Write a ~700-800 word spoken-word podcast script \
(about 5 minutes when read aloud) with this EXACT structure, in this order:

1. OPENING (2-3 sentences): brief, energetic greeting. State today's date EXACTLY \
as given here: "{date_str}" -- use this exact wording, do not recalculate or guess \
the weekday yourself.
2. TOP STORIES section: pick the 2-3 most important/exciting stories overall \
(breakthroughs, launches, major news). Give each a bit of room to breathe -- \
explain what happened and why it matters.
3. A short verbal transition sentence like "Now let's talk about what's moving \
in the startup and VC world."
4. VC & STARTUP MOVES section: pick 1-2 stories about company strategy, \
partnerships, new products, or notable people moves (NOT funding rounds).
5. A short verbal transition sentence like "And finally, the funding round-up."
6. FUNDING section: cover 2-3 funding rounds briefly and punchily -- company, \
amount, what they do, in one or two sentences each. Do not over-explain these.
7. CLOSING (1-2 sentences): short, warm sign-off.

Hard limits for the script:
- Maximum 7-8 stories total across all sections combined. Skip anything \
borderline or repetitive -- pick only the most interesting items, quality over quantity.
- Use natural spoken language (contractions, short sentences) -- NOT bullet points.
- The script text itself must be PURE spoken text -- no markdown, no headers, no \
bullet points, no section labels like "TOP STORIES" -- weave the structure in \
naturally through the spoken transitions instead.

Also write a short, punchy EPISODE TITLE (under 70 characters) that teases the \
single most interesting story of the day -- something a listener would want to \
click on in a podcast app. Do not just say "Deeptech Daily" -- give it real content, \
e.g. "SpaceX's New Engine Test + $40M for a Robotics Startup".

Respond with ONLY a raw JSON object, no markdown code fences, no preamble, in \
exactly this shape:
{{"title": "...", "script": "..."}}

Articles:
{articles}
"""


def build_articles_blob(articles):
    blob = ""
    for a in articles:
        blob += f"Source: {a['source']}\nTitle: {a['title']}\nSummary: {a['summary']}\nLink: {a['link']}\n\n"
    return blob


def _strip_code_fences(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text[: -3]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def generate_script(articles, date_str):
    """Returns a dict: {"title": str, "script": str}"""
    blob = build_articles_blob(articles)
    prompt = PROMPT_TEMPLATE.format(articles=blob, date_str=date_str)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1800,
        messages=[{"role": "user", "content": prompt}],
    )
    raw_text = message.content[0].text
    cleaned = _strip_code_fences(raw_text)
    try:
        data = json.loads(cleaned)
        return {"title": data["title"], "script": data["script"]}
    except (json.JSONDecodeError, KeyError) as e:
        # Fallback: falls das Parsen fehlschlaegt, den Rohtext als Skript nutzen
        print(f"Warning: could not parse JSON response ({e}), using raw text as script.")
        return {"title": f"Deeptech Daily — {date_str}", "script": raw_text}
