"""Daily SandeepAI Research digest mailer.

Reads the 6 site/data/*.json files, builds an HTML email summarising the top
papers per source, and sends it via SMTP.

Required env vars:
  SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, MAIL_FROM
Optional:
  MAIL_TO   (comma-separated; default = both hard-coded recipients)
  SITE_URL  (used for the 'Open the hub' link in the email footer)
"""

from __future__ import annotations

import json
import os
import smtplib
import ssl
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data"

DEFAULT_TO = [
    "Sandeep.chauhans@gmail.com",
    "Sandeep_singh@manulife.com",
]

TAB_ORDER = ["arxiv", "google", "microsoft", "openai", "anthropic", "meta"]


def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_section(tab_id: str, payload: dict, max_papers: int = 3) -> str:
    label = esc(payload.get("source", tab_id))
    src_url = esc(payload.get("source_url", ""))
    stamp = esc(payload.get("last_updated", ""))
    papers = payload.get("papers", [])[:max_papers]
    if not papers:
        return ""

    cards = []
    for p in papers:
        title = esc(p.get("title", "Untitled"))
        link = esc(p.get("link", "#"))
        summary = esc(p.get("summary", ""))[:600]
        bcase = p.get("insurance_business_case") or {}
        tech = p.get("technical_details") or {}
        bcase_html = ""
        if isinstance(bcase, dict) and bcase:
            head = esc(bcase.get("headline", ""))
            pts = "".join(f"<li>{esc(b)}</li>" for b in bcase.get("points", []))
            bcase_html = (
                f"<p style='margin:8px 0 4px;color:#2a3270'><strong>Insurance Business Case:</strong> {head}</p>"
                f"<ul style='margin:0 0 6px;padding-left:18px;color:#333'>{pts}</ul>"
            )
        tech_html = ""
        if isinstance(tech, dict) and tech:
            pat = esc(tech.get("pattern", ""))
            pts = "".join(f"<li>{esc(b)}</li>" for b in tech.get("points", []))
            tech_html = (
                f"<p style='margin:8px 0 4px;color:#7a225a'><strong>Technical Details:</strong> {pat}</p>"
                f"<ul style='margin:0;padding-left:18px;color:#333'>{pts}</ul>"
            )
        cards.append(
            f"""
            <tr><td style="padding:14px 16px;background:#ffffff;border:1px solid #e6e8f5;border-radius:12px;">
              <h3 style="margin:0 0 6px;font:600 16px/1.35 Segoe UI,Arial,sans-serif;">
                <a href="{link}" style="color:#1c2554;text-decoration:none">{title}</a>
              </h3>
              <p style="margin:0 0 6px;color:#555;font:14px/1.5 Segoe UI,Arial,sans-serif">{summary}</p>
              {bcase_html}
              {tech_html}
            </td></tr>
            <tr><td style="height:10px;line-height:10px;font-size:0">&nbsp;</td></tr>
            """
        )

    return f"""
      <h2 style="margin:24px 0 8px;font:700 18px/1.3 Segoe UI,Arial,sans-serif;color:#0b0e2a">
        {label} <span style="font-weight:400;color:#888;font-size:13px">· {stamp} · <a href="{src_url}" style="color:#5469d4">source</a></span>
      </h2>
      <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:separate;">{''.join(cards)}</table>
    """


def render_email(site_url: str) -> str:
    body_parts: list[str] = []
    for tab in TAB_ORDER:
        f = DATA / f"{tab}.json"
        if not f.exists():
            continue
        try:
            payload = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        body_parts.append(render_section(tab, payload))

    body = "".join(body_parts) or "<p>No data available today.</p>"
    return f"""<!doctype html><html><body style="margin:0;background:#f3f4fb;padding:24px;">
<div style="max-width:760px;margin:0 auto;background:#f3f4fb;font-family:Segoe UI,Arial,sans-serif;color:#1c2554">
  <h1 style="margin:0 0 6px;font:700 22px/1.2 Segoe UI,Arial,sans-serif;">SandeepAI Research — Daily Digest</h1>
  <p style="margin:0 0 18px;color:#555;font-size:14px">
    AI research, translated for Life &amp; Health insurance.
    Full hub: <a href="{esc(site_url)}" style="color:#5469d4">{esc(site_url)}</a>
  </p>
  {body}
  <p style="margin:28px 0 0;color:#888;font-size:12px;text-align:center">
    Sent by the SandeepAI Research bot. To stop, reply STOP.
  </p>
</div></body></html>"""


def send(html: str, recipients: Iterable[str]) -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "465"))
    user = os.environ["SMTP_USERNAME"]
    pwd = os.environ["SMTP_PASSWORD"]
    sender = os.environ.get("MAIL_FROM", user)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "SandeepAI Research — Daily AI Digest for L&H Insurance"
    msg["From"] = sender
    to_list = list(recipients)
    msg["To"] = ", ".join(to_list)
    msg.attach(MIMEText("HTML email — please view in an HTML-capable client.", "plain"))
    msg.attach(MIMEText(html, "html"))

    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as s:
            s.login(user, pwd)
            s.sendmail(sender, to_list, msg.as_string())
    else:
        with smtplib.SMTP(host, port) as s:
            s.ehlo(); s.starttls(context=ssl.create_default_context()); s.ehlo()
            s.login(user, pwd)
            s.sendmail(sender, to_list, msg.as_string())


def main() -> int:
    recipients_env = os.environ.get("MAIL_TO", "").strip()
    recipients = [r.strip() for r in recipients_env.split(",") if r.strip()] or DEFAULT_TO
    site_url = os.environ.get("SITE_URL", "https://SandeepAI.digitalplat.org")

    html = render_email(site_url)
    if os.environ.get("DRY_RUN") == "1":
        out = ROOT / "preview-email.html"
        out.write_text(html, encoding="utf-8")
        print(f"DRY_RUN=1 -> wrote {out}")
        return 0

    required = ["SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"missing env: {missing}", file=sys.stderr)
        return 1
    send(html, recipients)
    print(f"sent to {recipients}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
