"""Generic feed/HTML fetcher used by all 5 vendor sources.

Strategy:
  1. Try the source's RSS / Atom feed (most reliable).
  2. Fall back to scraping the HTML listing page with documented selectors.
  3. Always merge with existing JSON so hand-written insurance fields survive.
"""

from __future__ import annotations

import feedparser

from ._common import clean, http_get, merge_with_existing, soup, write_tab


def _strip_html(s: str) -> str:
    """Google News summaries are wrapped in <a>...</a><font>source</font> HTML."""
    if not s:
        return ""
    return clean(soup(s).get_text(" ", strip=True))


def from_feed(feed_url: str, *, source_tag: str, limit: int = 10) -> list[dict]:
    r = http_get(feed_url, accept="application/rss+xml, application/atom+xml, */*")
    feed = feedparser.parse(r.content)
    out: list[dict] = []
    for e in feed.entries[:limit]:
        title = clean(getattr(e, "title", ""))
        # Many feeds (incl. Google News) suffix the source name in the title; trim it.
        for tail in (f" - {source_tag}", f" — {source_tag}", f" | {source_tag}"):
            if title.endswith(tail):
                title = title[: -len(tail)].rstrip()
        out.append({
            "title": title,
            "link": clean(getattr(e, "link", "")),
            "authors": clean(getattr(e, "author", "")) or source_tag,
            "published": clean(getattr(e, "published", "") or getattr(e, "updated", ""))[:10],
            "summary": _strip_html(
                getattr(e, "summary", "") or getattr(e, "description", "")
            )[:1200],
            "tags": [t.term for t in getattr(e, "tags", [])][:5] or [source_tag],
        })
    return [p for p in out if p["title"] and p["link"]]


def from_html(page_url: str, *, item_selector: str, title_selector: str,
              link_selector: str | None = None, summary_selector: str | None = None,
              source_tag: str, limit: int = 8) -> list[dict]:
    r = http_get(page_url)
    page = soup(r.text)
    out: list[dict] = []
    for node in page.select(item_selector)[:limit * 3]:
        title_el = node.select_one(title_selector) if title_selector else node
        if not title_el:
            continue
        link_el = node.select_one(link_selector) if link_selector else title_el
        href = link_el.get("href") if link_el else None
        if not href:
            continue
        if href.startswith("/"):
            from urllib.parse import urlparse
            base = "{0.scheme}://{0.netloc}".format(urlparse(page_url))
            href = base + href
        summary_el = node.select_one(summary_selector) if summary_selector else None
        out.append({
            "title": clean(title_el.get_text()),
            "link": href,
            "authors": source_tag,
            "published": "",
            "summary": clean(summary_el.get_text()) if summary_el else "",
            "tags": [source_tag],
        })
        if len(out) >= limit:
            break
    return out


def run(tab_id: str, label: str, url: str, candidates: list[dict]) -> None:
    """`candidates` is an ordered list of strategies to try; first success wins."""
    last_err: Exception | None = None
    papers: list[dict] = []
    for strat in candidates:
        try:
            kind = strat.pop("kind")
            if kind == "feed":
                papers = from_feed(**strat)
            elif kind == "html":
                papers = from_html(**strat)
            if papers:
                break
        except Exception as e:
            last_err = e
            continue

    if not papers:
        print(f"[{tab_id}] all strategies failed (last error: {last_err}); "
              "keeping previously seeded data.")
        return

    merged = merge_with_existing(tab_id, papers, keep=10)
    out = write_tab(tab_id, label, url, merged)
    print(f"[{tab_id}] wrote {len(merged)} papers -> {out}")
