"""Utility for scraping university course catalogs.

The functions here provide a simple starting point for downloading and parsing
HTML-based course listings. You can extend or adapt them for specific
institution formats or to handle PDF sources.

Usage example::

    python -m utils.scrape_catalog https://catalog.utdallas.edu/now/courses/cs

The script will print a JSON object to stdout which you can save in
`data/<school>_cs.json` and then load from the backend.
"""

import json
import sys
from typing import Dict, List

import requests
from bs4 import BeautifulSoup


def fetch_catalog_html(url: str) -> str:
    """Download the HTML content of a catalog page."""
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text


def parse_table(html: str) -> Dict[str, Dict]:
    """Parse a simple table containing courses.

    This assumes each row has a course code, title, credits, and prerequisites.
    You may need to adapt the selectors for the university's layout.
    """
    soup = BeautifulSoup(html, "html.parser")
    data: Dict[str, Dict] = {}

    # example CSS selectors; adjust for target pages
    for row in soup.select("table.course-list tr"):
        cols = row.find_all("td")
        if len(cols) < 3:
            continue
        code = cols[0].get_text(strip=True)
        title = cols[1].get_text(strip=True)
        credits_text = cols[2].get_text(strip=True)
        try:
            credits = int(credits_text)
        except ValueError:
            credits = 0
        prereq_cells = cols[3].get_text(strip=True) if len(cols) > 3 else ""
        prereqs = [p.strip() for p in prereq_cells.split(",") if p.strip()]

        data[code] = {
            "name": title,
            "credits": credits,
            "prereqs": prereqs,
            "category": "core",  # default; adjust downstream
        }
    return data


def fetch_catalog(url: str) -> Dict[str, Dict]:
    html = fetch_catalog_html(url)
    return parse_table(html)


def main(url: str) -> None:
    """Command-line entry point."""
    catalog = fetch_catalog(url)
    json.dump(catalog, sys.stdout, indent=2)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m utils.scrape_catalog <catalog-url>")
        sys.exit(1)
    main(sys.argv[1])
