"""Enter a site name (e.g. example.com) and get a short summary of the site."""
import os
import sys
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import anthropic

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
MAX_CHARS = 12000
HEADERS = {"User-Agent": "Mozilla/5.0 (site-summarizer demo)"}


def normalize(site: str) -> str:
    site = site.strip()
    if not site.startswith(("http://", "https://")):
        site = "https://" + site
    parsed = urlparse(site)
    if not parsed.netloc or "." not in parsed.netloc:
        raise ValueError(f"'{site}' doesn't look like a valid site name")
    return site


def fetch_page(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.text


def extract_text(html: str):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta = soup.find("meta", attrs={"name": "description"})
    description = meta["content"].strip() if meta and meta.get("content") else ""
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())
    return title, description, text[:MAX_CHARS]


def summarize(url: str, title: str, description: str, text: str) -> str:
    prompt = (
        "Summarize this website in 4-5 sentences: what it is, who it is for, "
        "and its main offerings.\n\n"
        f"URL: {url}\nTitle: {title}\nMeta description: {description}\n\n"
        f"Page text:\n{text}"
    )
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    msg = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("Set the ANTHROPIC_API_KEY environment variable first.")

    site = input("Enter site name (e.g. example.com): ")
    try:
        url = normalize(site)
        html = fetch_page(url)
    except ValueError as e:
        sys.exit(str(e))
    except requests.RequestException as e:
        sys.exit(f"Could not load the site: {e}")

    title, description, text = extract_text(html)
    if not text:
        sys.exit("The page has no readable text (it may be rendered by JavaScript).")

    print("\nSummary of", url)
    print(summarize(url, title, description, text))


if __name__ == "__main__":
    main()
