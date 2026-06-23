import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

PROMPT_TEMPLATE = """You are the host of a short daily podcast called "Deeptech Daily" \
covering deeptech, robotics, and space startups.

Below are recent articles. Write a ~700-800 word spoken-word podcast script \
(about 5 minutes when read aloud) with this EXACT structure, in this order:

1. OPENING (2-3 sentences): brief, energetic greeting and today's date ({date_str}).
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

Hard limits:
- Maximum 7-8 stories total across all sections combined. Skip anything \
borderline or repetitive -- pick only the most interesting items, quality over quantity.
- Use natural spoken language (contractions, short sentences) -- NOT bullet points.
- Output PURE spoken script text only -- no markdown, no headers, no bullet points, \
no section labels like "TOP STORIES" -- weave the structure in naturally through \
the spoken transitions instead.

Articles:
{articles}
"""


def build_articles_blob(articles):
    blob = ""
    for a in articles:
        blob += f"Source: {a['source']}\nTitle: {a['title']}\nSummary: {a['summary']}\nLink: {a['link']}\n\n"
    return blob


def generate_script(articles, date_str):
    blob = build_articles_blob(articles)
    prompt = PROMPT_TEMPLATE.format(articles=blob, date_str=date_str)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
