"""Fetch all six tabs.

Usage:  py -3 scripts/fetch_all.py
"""

from __future__ import annotations

from sources import arxiv as src_arxiv
from sources.vendor import run as vendor_run


def fetch_arxiv():
    src_arxiv.main()


def fetch_google():
    vendor_run(
        "google", "Google-AI", "https://ai.google/research/",
        [
            {"kind": "feed", "feed_url": "https://blog.google/technology/ai/rss/", "source_tag": "Google AI Blog"},
            {"kind": "feed", "feed_url": "https://deepmind.google/blog/rss.xml",   "source_tag": "Google DeepMind"},
        ],
    )


def fetch_microsoft():
    vendor_run(
        "microsoft", "Microsoft-AI",
        "https://www.microsoft.com/en-us/research/research-area/artificial-intelligence/",
        [
            {"kind": "feed",
             "feed_url": "https://www.microsoft.com/en-us/research/feed/?research_area=13556",
             "source_tag": "Microsoft Research"},
            {"kind": "feed", "feed_url": "https://www.microsoft.com/en-us/research/feed/", "source_tag": "Microsoft Research"},
        ],
    )


def fetch_openai():
    vendor_run(
        "openai", "OpenAI-AI", "https://openai.com/research/",
        [
            {"kind": "html",
             "page_url": "https://openai.com/research/",
             "item_selector": "a[href*='/index/'], a[href*='/research/']",
             "title_selector": "h3, h2",
             "summary_selector": "p",
             "source_tag": "OpenAI"},
        ],
    )


def fetch_anthropic():
    vendor_run(
        "anthropic", "Anthropic-AI", "https://www.anthropic.com/research",
        [
            {"kind": "feed", "feed_url": "https://www.anthropic.com/news/rss.xml", "source_tag": "Anthropic"},
            {"kind": "html",
             "page_url": "https://www.anthropic.com/research",
             "item_selector": "a[href*='/research/'], a[href*='/news/']",
             "title_selector": "h3, h2",
             "summary_selector": "p",
             "source_tag": "Anthropic"},
        ],
    )


def fetch_meta():
    vendor_run(
        "meta", "Meta-AI", "https://ai.meta.com/research/",
        [
            {"kind": "feed", "feed_url": "https://ai.meta.com/blog/rss/", "source_tag": "Meta AI"},
            {"kind": "html",
             "page_url": "https://ai.meta.com/research/",
             "item_selector": "a[href*='/research/publications/'], a[href*='/blog/']",
             "title_selector": "h3, h2",
             "summary_selector": "p",
             "source_tag": "Meta AI"},
        ],
    )


def main() -> int:
    fetchers = [
        ("arxiv",     fetch_arxiv),
        ("google",    fetch_google),
        ("microsoft", fetch_microsoft),
        ("openai",    fetch_openai),
        ("anthropic", fetch_anthropic),
        ("meta",      fetch_meta),
    ]
    failed = 0
    for name, fn in fetchers:
        try:
            fn()
        except Exception as e:
            failed += 1
            print(f"[{name}] FAILED: {e}")
    print(f"done. failures: {failed}/{len(fetchers)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    raise SystemExit(main())
