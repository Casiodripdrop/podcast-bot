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
- If there are fewer articles than usual, simply cover all of them in more depth \
and spend a bit longer on context/why-it-matters for each one -- the episode can \
run a bit shorter than 5 minutes if needed. NEVER mention the number of available \
articles, never apologize for thin content, never comment on the article supply at \
all -- the listener should never know how many sources you had. Just deliver a \
normal-sounding episode with whatever is given.
- NEVER invent or guess specific facts that are not present in the articles below \
-- no invented funding amounts, investor names, founder names, dates, or product \
details. If an article's summary is vague, describe it at that same level of \
generality (e.g. "raised a new funding round" instead of guessing a dollar figure) \
or add only well-established general background knowledge, never fabricated specifics.

Also write a short, punchy EPISODE TITLE (under 70 characters) that teases the \
single most interesting story of the day -- something a listener would want to \
click on in a podcast app. Do not just say "Deeptech Daily" -- give it real content, \
e.g. "SpaceX's New Engine Test + $40M for a Robotics Startup".

CRITICAL OUTPUT FORMAT: Respond with ONLY a single raw JSON object and absolutely \
nothing else -- no preamble, no notes, no commentary before or after, no markdown \
code fences. Your entire response must be parseable directly as JSON, in exactly \
this shape:
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


class ScriptGenerationError(Exception):
    """Wird ausgeloest, wenn Claude kein gueltiges JSON liefert -- dann lieber \
    die Episode fuer heute auslassen, statt kaputten/unbeabsichtigten Text \
    (z.B. Meta-Kommentare) zu veroeffentlichen."""
    pass


def generate_script(articles, date_str):
    """Returns a dict: {"title": str, "script": str}. Wirft ScriptGenerationError \
    falls die Antwort nicht als JSON parsbar ist, statt unsicheren Rohtext zu nutzen."""
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
        title = data["title"]
        script = data["script"]
        if not title.strip() or not script.strip():
            raise ValueError("title or script is empty")
        return {"title": title, "script": script}
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Error: could not parse a valid script from Claude's response ({e}).")
        print(f"Raw response was:\n{raw_text[:500]}")
        raise ScriptGenerationError(str(e)) from e
