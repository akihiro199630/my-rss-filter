import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator


USER_AGENT = "RSS-Image-Filter/1.0"
OUTPUT_PATH = Path("public/filtered_rss.xml")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def get_target_words():
    configured_words = os.getenv("TARGET_ALT_TEXT") or "〇〇"
    return [word.strip() for word in configured_words.split(",") if word.strip()]


def get_source_rss_url():
    source_rss_url = os.getenv("SOURCE_RSS_URL", "").strip()
    parsed_url = urlparse(source_rss_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError(
            "Set SOURCE_RSS_URL to the full HTTP or HTTPS URL of the source RSS feed."
        )
    return source_rss_url


def article_has_target_alt(article_url, target_words, session):
    response = session.get(
        article_url,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    contents = soup.select_one("#contents")
    if contents is None:
        return False

    return any(
        word in image.get("alt", "")
        for image in contents.find_all("img")
        for word in target_words
    )


def copy_entry(source_entry, destination_feed):
    entry = destination_feed.add_entry()

    entry_id = source_entry.get("id") or source_entry.get("link")
    if entry_id:
        entry.id(entry_id)

    title = source_entry.get("title")
    if title:
        entry.title(title)

    link = source_entry.get("link")
    if link:
        entry.link(href=link, rel="alternate")

    description = source_entry.get("summary") or source_entry.get("description")
    if description:
        entry.description(description)

    for date_name in ("published", "updated"):
        date_value = source_entry.get(date_name)
        parsed_date = source_entry.get(f"{date_name}_parsed")
        if parsed_date:
            date_value = datetime(*parsed_date[:6], tzinfo=timezone.utc)
        if date_value:
            getattr(entry, date_name)(date_value)

    if source_entry.get("author"):
        entry.author(name=source_entry.author)

    for category in source_entry.get("tags", []):
        term = category.get("term")
        if term:
            entry.category(term=term)


def main():
    target_words = get_target_words()
    source_rss_url = get_source_rss_url()

    with requests.Session() as session:
        session.headers.update({"User-Agent": USER_AGENT})
        response = session.get(source_rss_url, timeout=30)
        response.raise_for_status()

        source_feed = feedparser.parse(response.content)
        if source_feed.bozo:
            raise ValueError(f"Failed to parse source RSS: {source_feed.bozo_exception}")

        filtered_feed = FeedGenerator()
        filtered_feed.title(source_feed.feed.get("title", "Filtered RSS Feed"))
        filtered_feed.link(href=source_rss_url, rel="alternate")
        filtered_feed.description(
            source_feed.feed.get("description", "Filtered RSS feed")
        )

        entries = source_feed.entries
        excluded_count = 0
        for index, source_entry in enumerate(entries):
            article_url = source_entry.get("link")
            if not article_url:
                logging.warning("Skipping RSS entry without an article URL.")
                continue

            if index > 0:
                time.sleep(1)

            try:
                should_exclude = article_has_target_alt(
                    article_url,
                    target_words,
                    session,
                )
            except requests.RequestException as error:
                logging.warning(
                    "Could not inspect an article; keeping it in the feed (%s).",
                    type(error).__name__,
                )
                should_exclude = False

            if should_exclude:
                excluded_count += 1
            else:
                copy_entry(source_entry, filtered_feed)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    filtered_feed.rss_file(str(OUTPUT_PATH), pretty=True)
    logging.info(
        "Wrote filtered RSS (%d articles excluded).",
        excluded_count,
    )


if __name__ == "__main__":
    main()
