"""Shared helpers for SandeepAI fetch scripts."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "site" / "data"

USER_AGENT = (
    "SandeepAI-Research/1.0 (+https://SandeepAI.digitalplat.org)"
    " research-aggregator; contact: Sandeep_singh@manulife.com"
)


def http_get(url: str, *, timeout: int = 30, accept: str | None = None) -> requests.Response:
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r


def soup(text: str) -> BeautifulSoup:
    return BeautifulSoup(text, "lxml")


def clean(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def write_tab(tab_id: str, source_label: str, source_url: str, papers: list[dict[str, Any]]) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": source_label,
        "source_url": source_url,
        "last_updated": today(),
        "papers": papers,
    }
    out = DATA_DIR / f"{tab_id}.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def merge_with_existing(tab_id: str, new_papers: list[dict[str, Any]], keep: int = 10) -> list[dict[str, Any]]:
    """Merge by link, newest first, preserve any hand-written insurance fields."""
    existing_file = DATA_DIR / f"{tab_id}.json"
    existing: dict[str, dict[str, Any]] = {}
    if existing_file.exists():
        try:
            for p in json.loads(existing_file.read_text(encoding="utf-8")).get("papers", []):
                if p.get("link"):
                    existing[p["link"]] = p
        except Exception:
            pass

    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for p in new_papers:
        link = p.get("link") or p.get("title")
        if not link or link in seen:
            continue
        seen.add(link)
        old = existing.get(link, {})
        # Preserve hand-written / LLM-enriched fields
        for k in ("insurance_business_case", "technical_details", "tags"):
            if k in old and k not in p:
                p[k] = old[k]
        merged.append(p)

    # Backfill with anything still in existing that we didn't see this run
    for link, p in existing.items():
        if link not in seen:
            merged.append(p)
            seen.add(link)

    return merged[:keep]
