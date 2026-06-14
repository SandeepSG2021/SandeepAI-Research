"""Enrich each paper in site/data/*.json with an Insurance Business Case
and Technical Details, via the OpenAI Chat Completions API.

Skips papers that already have BOTH fields (so re-runs are cheap).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    from openai import OpenAI  # type: ignore
except Exception as e:  # pragma: no cover
    OpenAI = None  # type: ignore
    _import_err = e

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data"

SYSTEM = (
    "You are a Senior Enterprise AI Architect and L&H Insurance subject-matter expert. "
    "Translate AI research into (a) the concrete Life & Health insurance business case "
    "(underwriting, claims, distribution, customer, operations, risk) and "
    "(b) the technical pattern an architecture team would implement. "
    "Be concrete, specific, and avoid generic management speak."
)

USER_TEMPLATE = """Paper title: {title}
Source: {source}
Summary / abstract:
{summary}

Return a JSON object with this exact shape — no markdown, no commentary:
{{
  "insurance_business_case": {{
    "headline": "<one sentence why this matters to a L&H insurer>",
    "points": ["<bullet>", "<bullet>", "<bullet>"]
  }},
  "technical_details": {{
    "pattern": "<one-line architectural pattern>",
    "points": ["<concrete implementation bullet>", "<bullet>", "<bullet>", "<bullet>"]
  }}
}}

Constraints:
- 3-5 bullets per list, each <= 30 words.
- Reference specific insurance systems / regulations / personas where applicable
  (e.g. policy admin, Guidewire, OSFI E-23, NAIC, SR 11-7, IFRS 17, FNOL).
- Technical bullets must mention concrete tech (RAG, MCP, vector DB, LoRA, ONNX, etc.)
  and at least one governance / risk control."""


def needs_enrichment(p: dict) -> bool:
    return not (p.get("insurance_business_case") and p.get("technical_details"))


def enrich_one(client, model: str, source: str, paper: dict) -> dict | None:
    if not paper.get("summary"):
        return None
    prompt = USER_TEMPLATE.format(
        title=paper.get("title", ""), source=source, summary=paper["summary"]
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or "{}"
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


def main() -> int:
    if OpenAI is None:
        print(f"openai package missing: {_import_err}", file=sys.stderr)
        return 1
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set — enrichment skipped (seed data preserved).")
        return 0

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI()
    total_enriched = 0
    for f in sorted(DATA.glob("*.json")):
        payload = json.loads(f.read_text(encoding="utf-8"))
        changed = False
        for p in payload.get("papers", []):
            if not needs_enrichment(p):
                continue
            print(f"[{f.stem}] enriching: {p.get('title','')[:60]}…")
            try:
                got = enrich_one(client, model, payload.get("source", f.stem), p)
            except Exception as e:
                print(f"  -> failed: {e}")
                continue
            if got and got.get("insurance_business_case") and got.get("technical_details"):
                p["insurance_business_case"] = got["insurance_business_case"]
                p["technical_details"] = got["technical_details"]
                total_enriched += 1
                changed = True
        if changed:
            f.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"enrichment complete. papers enriched this run: {total_enriched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
