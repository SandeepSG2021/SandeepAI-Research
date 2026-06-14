# Deployment — `SandeepAI.dpdns.org` via GitHub Pages

This site is **static** (HTML + CSS + JS + JSON) and ships from the
`site/` folder of this repo to **GitHub Pages**, then is fronted by a free
DigitalPlat subdomain (`SandeepAI.dpdns.org`).

The repo URL is **https://github.com/SandeepSG2021/SandeepAI-Research**.
The Pages URL (always works, even before DNS) is
**https://sandeepsg2021.github.io/SandeepAI-Research/**.
The custom-domain URL (once DNS is in place) is
**https://SandeepAI.dpdns.org**.

---

## Status checklist

| # | Step                                                           | Owner | Status |
| - | -------------------------------------------------------------- | ----- | ------ |
| 1 | Push repo to GitHub                                            | bot   | done   |
| 2 | Enable GitHub Pages from `/site` on `main`                     | bot   | done   |
| 3 | Add `CNAME` file with `SandeepAI.dpdns.org`                    | bot   | done   |
| 4 | Register `SandeepAI.dpdns.org` and point CNAME at GitHub Pages | YOU   | TODO   |
| 5 | Add GitHub Actions secrets (OpenAI + SMTP)                     | YOU   | TODO   |
| 6 | Confirm first scheduled run sends email                        | both  | TODO   |

---

## 4 ▸ Register `SandeepAI.dpdns.org`  *(YOU MUST DO)*

1. Open https://dash.domain.digitalplat.org/ and sign in with GitHub.
2. **Register Domain** → choose TLD `dpdns.org` → enter prefix `SandeepAI`.
3. After approval (usually minutes), open the domain's **DNS panel**
   and add a single record:

   | Type  | Name  | Value                         | TTL  |
   | ----- | ----- | ----------------------------- | ---- |
   | CNAME | `@`   | `sandeepsg2021.github.io`     | Auto |

4. (Optional but recommended) Also add the four GitHub Pages apex A
   records, in case DigitalPlat blocks apex-CNAME:

   | Type | Name | Value          |
   | ---- | ---- | -------------- |
   | A    | `@`  | 185.199.108.153|
   | A    | `@`  | 185.199.109.153|
   | A    | `@`  | 185.199.110.153|
   | A    | `@`  | 185.199.111.153|

5. Wait 5–60 minutes for DNS to propagate. Test:
   ```powershell
   nslookup SandeepAI.dpdns.org 1.1.1.1
   ```

6. GitHub will automatically issue a Let's Encrypt cert. To force a
   re-check from the CLI:
   ```powershell
   gh api -X PUT /repos/SandeepSG2021/SandeepAI-Research/pages -f cname=SandeepAI.dpdns.org -F https_enforced=true
   ```

---

## 5 ▸ Configure GitHub Actions secrets  *(YOU MUST DO)*

The daily workflow needs an OpenAI key and SMTP credentials. **Run these
commands in PowerShell** — `gh` will prompt for each value securely (the
secret is sent over TLS to GitHub and never appears in your shell history
when you press Enter on the prompt). Replace the placeholder names with
your own — do **not** type the secret on the command line.

```powershell
$repo = "SandeepSG2021/SandeepAI-Research"

# OpenAI (used to enrich each paper with the Insurance Business Case)
gh secret set OPENAI_API_KEY  --repo $repo            # paste sk-...

# SMTP — Gmail App Password is the easiest (https://myaccount.google.com/apppasswords)
gh secret set SMTP_HOST       --repo $repo --body "smtp.gmail.com"
gh secret set SMTP_PORT       --repo $repo --body "465"
gh secret set SMTP_USERNAME   --repo $repo            # paste your gmail address
gh secret set SMTP_PASSWORD   --repo $repo            # paste the 16-char App Password
gh secret set MAIL_FROM       --repo $repo --body "SandeepAI Briefing <YOUR_GMAIL@gmail.com>"
```

> The `MAIL_TO` value is already hard-coded in the workflow to
> `Sandeep.chauhans@gmail.com,Sandeep_singh@manulife.com`.

Then trigger a one-off run to verify:

```powershell
gh workflow run "SandeepAI Daily Update" --repo $repo
gh run watch --repo $repo
```

The action will: fetch all 6 sources → enrich with the insurance angle →
commit the refreshed JSON back to `main` (which auto-rebuilds Pages) →
email both recipients.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `404 Not Found` at the Pages URL | Pages not enabled, or build still running | `gh api /repos/SandeepSG2021/SandeepAI-Research/pages` to inspect; first build takes ~1 min |
| `DNS_PROBE_FINISHED_NXDOMAIN` for `SandeepAI.dpdns.org` | Domain not yet approved, or CNAME missing | Re-check DigitalPlat dashboard; `nslookup` until it resolves |
| Pages serves HTTP but cert is pending | Cert needs DNS to resolve first | Wait 10 min, then enforce HTTPS via the `gh api` command above |
| Email never arrives | Wrong SMTP, or Manulife inbox quarantine | Open the Action run logs; check Junk; whitelist `MAIL_FROM` |
| Vendor fetcher returns 0 papers | Site redesigned, selectors stale | Update strategy in `scripts/fetch_all.py` (RSS first, HTML fallback) |
