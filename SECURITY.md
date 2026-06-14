# Reporting a vulnerability

If you believe you've found a security issue in this repository:

- **Do not** open a public issue.
- Use GitHub's private vulnerability reporting:
  https://github.com/SandeepSG2021/SandeepAI-Research/security/advisories/new

We will acknowledge within a few days. No bug bounty.

## What this project handles

- **Public data only.** The site renders publicly-available AI research
  paper metadata. No personal data, no customer data, no credentials live
  in this repo.
- Secrets (`OPENAI_API_KEY`, SMTP credentials) live exclusively in
  GitHub Actions repository secrets — never in source, `.env` files, or
  workflow logs.
- The site is a static page; there is no backend, no database, no auth.

## Hardening already in place

- All Python dependencies pinned in [requirements.txt](requirements.txt);
  Dependabot opens PRs weekly for security updates.
- Workflows declare `permissions:` with least-privilege scopes.
- `concurrency:` locks prevent racing pushes to `main`.
- Every outbound HTTP call has connect + read timeouts and verifies TLS
  certs (the requests-library default — never disabled).
- The user-agent string does not leak personal contact info.
- SMTP send always uses TLS (SMTPS on 465 or STARTTLS on 587).
- No third-party scripts/trackers are loaded on the front-end.
