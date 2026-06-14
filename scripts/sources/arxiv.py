"""arXiv cs.AI fetcher — uses the official Atom API (stable, no scraping)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from ._common import clean, http_get, merge_with_existing, write_tab

API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}

TAB_ID = "arxiv"
LABEL = "ARXIV-AI"
URL = "https://arxiv.org/list/cs.AI/recent"


def fetch(max_results: int = 15) -> list[dict]:
    params = (
        f"search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending"
        f"&start=0&max_results={max_results}"
    )
    r = http_get(f"{API}?{params}")
    root = ET.fromstring(r.text)
    out: list[dict] = []
    for entry in root.findall("a:entry", NS):
        out.append({
            "title": clean(entry.findtext("a:title", "", NS)),
            "link": clean(entry.findtext("a:id", "", NS)),
            "authors": ", ".join(
                clean(a.findtext("a:name", "", NS)) for a in entry.findall("a:author", NS)
            )[:240],
            "published": clean(entry.findtext("a:published", "", NS))[:10],
            "summary": clean(entry.findtext("a:summary", "", NS))[:1200],
            "tags": ["cs.AI"],
        })
    return out


def main() -> None:
    papers = merge_with_existing(TAB_ID, fetch(), keep=10)
    out = write_tab(TAB_ID, LABEL, URL, papers)
    print(f"[arxiv] wrote {len(papers)} papers -> {out}")


if __name__ == "__main__":
    main()
