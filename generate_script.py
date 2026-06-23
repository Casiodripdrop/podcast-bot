import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

PROMPT_TEMPLATE = """You are the host of a short daily podcast called "Deeptech Daily" \
covering deeptech, robotics, and space startups.

Below are recent articles. Write a ~700-800 word spoken-word podcast script \
(about 5 minutes when read aloud) that:
- Opens with a brief, energetic greeting and today's date ({date_str})
- Covers the 4-6 most interesting/important stories, grouped naturally (not a list)
- Briefly explains WHY each story matters for the space/robotics/deeptech startup scene
- Uses natural spoken language (contractions, short sentences) -- NOT bullet points
- Closes with a short, warm sign-off
- Output PURE spoken script text only -- no markdown, no headers, no bullet points

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
