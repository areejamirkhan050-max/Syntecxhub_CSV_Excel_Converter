"""
Web Scraper for Headlines
Syntecxhub Internship - Task 3, Project 2
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import logging
import sys
import argparse
from datetime import datetime
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

NEWS_SOURCES = {
    "bbc": {
        "url": "https://www.bbc.com/news",
        "headline_tag": "h3",
        "headline_class": None,
        "link_tag": "a",
    },
    "hnews": {
        "url": "https://news.ycombinator.com",
        "headline_tag": "span",
        "headline_class": "titleline",
        "link_tag": "a",
    }
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}

def is_allowed(url):
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch("*", url)
    except Exception:
        return True

def fetch_page(url, retries=3, delay=2):
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Fetching: {url} (attempt {attempt})")
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error: {e}")
            if attempt < retries:
                time.sleep(delay)
    return None

def parse_headlines(html, base_url, source_config, keyword=None):
    soup = BeautifulSoup(html, "html.parser")
    headlines = []
    tag = source_config.get("headline_tag", "h3")
    cls = source_config.get("headline_class")
    elements = soup.find_all(tag, class_=cls) if cls else soup.find_all(tag)
    seen = set()
    for el in elements:
        title = el.get_text(strip=True)
        if not title or len(title) < 10:
            continue
        if keyword and keyword.lower() not in title.lower():
            continue
        if title in seen:
            continue
        seen.add(title)
        link_el = el.find("a") or el.find_parent("a")
        url = ""
        if link_el and link_el.get("href"):
            href = link_el["href"]
            url = href if href.startswith("http") else urljoin(base_url, href)
        headlines.append({
            "title": title,
            "url": url,
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": base_url
        })
    logger.info(f"Found {len(headlines)} headlines.")
    return headlines

def save_to_json(data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved to JSON: {output_path}")

def save_to_csv(data, output_path):
    if not data:
        return
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "url", "scraped_at", "source"])
        writer.writeheader()
        writer.writerows(data)
    logger.info(f"Saved to CSV: {output_path}")

def scrape(sources, keyword=None, output_format="json", output_file="headlines"):
    all_headlines = []
    for source_name in sources:
        if source_name not in NEWS_SOURCES:
            logger.warning(f"Unknown source: {source_name}")
            continue
        config = NEWS_SOURCES[source_name]
        url = config["url"]
        if not is_allowed(url):
            continue
        html = fetch_page(url)
        if not html:
            continue
        headlines = parse_headlines(html, url, config, keyword=keyword)
        all_headlines.extend(headlines)
        time.sleep(2)
    print("\n" + "="*60)
    print(f"  SCRAPED HEADLINES ({len(all_headlines)} total)")
    print("="*60)
    for i, h in enumerate(all_headlines[:20], 1):
        print(f"\n{i}. {h['title']}")
        if h['url']:
            print(f"   URL: {h['url']}")
    print("="*60)
    if output_format == "csv":
        save_to_csv(all_headlines, f"{output_file}.csv")
    else:
        save_to_json(all_headlines, f"{output_file}.json")

def parse_args():
    parser = argparse.ArgumentParser(description="Web Scraper | Syntecxhub Task 3 Project 2")
    parser.add_argument("--sources", nargs="+", default=["hnews"])
    parser.add_argument("--keyword", default=None)
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    parser.add_argument("--output", default="headlines")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    logger.info("Web Scraper | Syntecxhub Task 3 Project 2")
    scrape(args.sources, args.keyword, args.format, args.output)