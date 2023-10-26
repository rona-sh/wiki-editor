import requests
import re
import sys

import mydb
import openai
import wikipediaapi
from bs4 import BeautifulSoup


def get_article(session):
    en_wiki = wikipediaapi.Wikipedia("Testing", "en")
    while True:
        r = session.get("https://en.wikipedia.org/w/index.php?title=Special:Random&action=edit")
        if "short description" in r.text.lower():
            continue
        title = re.findall("<title>View source for (.*?) - Wikipedia</title>", r.text)[0]
        page = en_wiki.page(title)
        summary = page.summary
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful Wikipedia editor."},
                {
                    "role": "user",
                    "content": "Below is a summary of a Wikipedia article. Write the content for a {{Short description}} template using no more than 7 words. Make it short.\n\n"
                    + summary,
                },
            ],
        )
        resp = response["choices"][0]["message"]["content"].rstrip(".")
        return {
            "title": title,
            "url": page.fullurl,
            "summary": summary,
            "suggested_summary": resp,
        }


def add_articles(n):
    session = requests.session()
    with mydb.Connection(name="wiki") as conn:
        for _ in range(n):
            a = get_article(session)
            print("{:<50} {}".format(a["title"], a["suggested_summary"]))
            conn.insert_dict("wiki_sd", a)


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        command = sys.argv[1]
        if command == "add_articles":
            add_articles(int(sys.argv[2]))
        else:
            assert False, f"Error: Unknown command '{command}'"
