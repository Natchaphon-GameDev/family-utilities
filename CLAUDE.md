# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Family utilities, published as a static GitHub Pages site from the repo root (`.nojekyll`, no build step).
Live at https://natchaphon-gamedev.github.io/family-utilities/ (repo `Natchaphon-GameDev/family-utilities`). **The repo is public.**

Current project: an SCB Home Loan dashboard built from the receipt PDFs that SCB emails each month (Dad forwards them).

## Commands

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # one-time setup
.venv/bin/python extract.py        # decrypt receipts/*.PDF and rewrite data.json
python3 -m http.server             # view index.html locally (fetch() fails over file://)
bash .claude/skills/refresh-dashboard/publish.sh   # extract + leak check + commit data.json + push + wait for Pages
```

There are no tests or linters. To refresh with new receipts end to end, use the `/refresh-dashboard` skill (`.claude/skills/refresh-dashboard/SKILL.md`): it finds new receipts in Gmail, downloads them through Chrome (the Gmail connector can't download attachments), then runs `publish.sh`.

## Data flow

1. `receipts/*.PDF` (gitignored): password-protected SCB receipts named `MG-<account>-<receiptno>-E-YYYYMMDD.PDF`. The password is `SCB_PDF_PASSWORD` in `.env` (gitignored). Never print it or ask for it in chat.
2. `extract.py` decrypts each PDF with pypdf and pulls fields out of the extracted text with regexes anchored on the English labels (`(Date)`, `(Interest Rate)`, `(No.)`, `(Baht)`, `(Total)`). If SCB changes the layout, dump the text the same way and adjust `parse_receipt`. `other` is derived as `total - principal - interest` so fees and insurance are caught without parsing them.
3. Receipts are deduped by receipt number, **not** by month. SCB can split one month into several receipts, and each one is kept.
4. `contract.json` holds hand-entered contract terms (from the scanned PDF in `contract/`, gitignored). `extract.py` merges it into `data.json` as `{contract, receipts}`.
5. `index.html` is a single self-contained file (inline CSS and JS, hand-rolled SVG charts, no libraries) that does `fetch("data.json")`. `byMonth()` sums receipts per month for the charts, and balance/rate/date come from the month's last receipt. Payoff projections assume each future month pays the contract's required installment plus the average extra paid so far, at the latest rate. The page has an EN/TH toggle (`L` dictionary in `index.html`; Thai uses Buddhist-era years), so any new user-facing string needs both languages.

## Privacy constraint

Only `data.json`, `contract.json`, and `index.html` get published. The full loan account number appears in receipt and contract filenames and must never reach a tracked file. `contract.json` stores it masked (`••••1149`). `publish.sh` aborts if the full number shows up in any tracked file or in `data.json`. If it prints `ABORT`, stop and report it; do not work around it. `publish.sh` stages and commits only `data.json`.
