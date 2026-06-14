# SandeepAI Research — Liquid Glass AI Paper Hub

A Liquid-Glass UI web app that tracks the latest research from **6 AI sources**
(arXiv, Google, Microsoft, OpenAI, Anthropic, Meta), then translates each paper
into a **Life & Health Insurance** business case + technical blueprint.

- Daily email digest to `Sandeep.chauhans@gmail.com` and `Sandeep_singh@manulife.com`
- Static front-end hosted on **GitHub Pages** from the `site/` folder
- Free public domain target: **`SandeepAI.dpdns.org`** (registered free at https://dash.domain.digitalplat.org/)

```
SandeepAI-Research/
├── site/                  # The static site that gets deployed
│   ├── index.html
│   ├── assets/{style.css, app.js, glass-bg.svg}
│   └── data/              # JSON consumed by the UI (1 file per tab + meta)
├── scripts/
│   ├── fetch_all.py       # 1 entry-point — refreshes all 6 JSON files
│   ├── sources/           # one module per source (arxiv, google, ...)
│   ├── enrich.py          # adds Insurance Business Case + Technical Details via LLM
│   └── send_email.py      # daily digest mailer (SMTP)
├── deploy/
│   └── DEPLOY.md          # GitHub Pages + DigitalPlat dashboard setup
├── .github/workflows/
│   └── daily-update.yml   # cron: fetch → enrich → commit → email
├── requirements.txt
├── .env.example
└── README.md (this file)
```

## Quick start (local preview)

```powershell
cd "C:\Users\singsas\OneDrive - Manulife\0000-20-Coding\RESEARCH\SandeepAI-Research"
py -3 -m http.server 8080 --directory site
# open http://localhost:8080
```

The site ships with **seed data** (4–6 real recent papers per tab, each with a
hand-written Insurance business case) so it looks complete on first load.

## Refresh the data manually

```powershell
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
$env:OPENAI_API_KEY = "sk-..."   # required only for the enrichment step
py -3 scripts/fetch_all.py
py -3 scripts/enrich.py           # adds Insurance Business Case + Technical Details
```

## Send the daily email manually

```powershell
$env:SMTP_HOST = "smtp.gmail.com"
$env:SMTP_PORT = "465"
$env:SMTP_USERNAME = "youraddress@gmail.com"
$env:SMTP_PASSWORD = "<gmail app password>"
$env:MAIL_FROM = "SandeepAI Briefing <youraddress@gmail.com>"
py -3 scripts/send_email.py
```

## Automated daily run

Push the repo to GitHub. The workflow at `.github/workflows/daily-update.yml`
runs **every day at 11:00 UTC (07:00 ET)** and:
1. Re-fetches all 6 sources.
2. Re-enriches with the Insurance angle.
3. Commits the new JSON back to `main`.
4. Cloudflare Pages auto-deploys `site/` to `SandeepAI.digitalplat.org`.
5. Emails both recipients with the day's top papers.

Set repository **secrets**: `OPENAI_API_KEY`, `SMTP_HOST`, `SMTP_PORT`,
`SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_FROM`.

## Deployment

See [deploy/DEPLOY.md](deploy/DEPLOY.md). One manual step remains for you
(the rest is automated):

1. **Register `SandeepAI.dpdns.org`** at https://dash.domain.digitalplat.org/
   and create a `CNAME` record pointing to `sandeepsg2021.github.io`.
   (GitHub Pages auto-issues an SSL cert once DNS resolves.)

## Honest limitations

- LLM enrichment requires an `OPENAI_API_KEY` and outbound access to
  `api.openai.com` — Manulife corporate proxy may block this on-network. Run
  enrichment in GitHub Actions instead.
- DigitalPlat FreeDomain approval is a manual PR review (usually < 24 h).
- The 6 vendor sites (Google/Microsoft/OpenAI/Anthropic/Meta) have no public
  research API. The scraper uses each site's public RSS / Atom / sitemap feed
  where available, and falls back to HTML parsing — selectors may need
  occasional maintenance when the sites redesign.
