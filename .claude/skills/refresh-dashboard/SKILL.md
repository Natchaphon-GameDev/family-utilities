---
name: refresh-dashboard
description: Pull the newest SCB Home Loan receipt PDFs that Dad forwarded to Gmail, rebuild data.json, and redeploy the GitHub Pages dashboard. Use when the user says "refresh dashboard", "update the loan data", "pull latest receipt", or runs /refresh-dashboard.
---

# Refresh the SCB Home Loan dashboard

Running this skill is the user's explicit request to download the new receipts, commit `data.json`, and push it to the public site. Commit nothing else.

## 1. Find receipts in Gmail

Search with `search_threads` (all time, `pageSize` 50, follow `pageToken`):

```
(from:narongsi@greenspot.co.th OR from:SCBMG.eMaildocument@email.scb.co.th) subject:"SCB Home Loan" has:attachment
```

For each thread, call `get_thread` with `messageFormat: PLAIN_TEXT`. `MINIMAL` and `METADATA_ONLY` leave out attachments. Collect the attachment filenames (`MG-...-E-YYYYMMDD.PDF`) and the `viewUrl`. SCB can send several receipts in one month (split payments), all with the same subject line, so check every thread's attachment filename. Two filenames are the same receipt only if they match exactly.

Compare with `ls receipts/`. Only the filenames not already there are new. If nothing is new, skip to step 3: the script exits early if `data.json` is unchanged.

## 2. Download new PDFs (Claude in Chrome)

The Gmail connector cannot download attachments, so use the browser.

1. Load the Chrome tools in one ToolSearch call, then call `tabs_context_mcp` with `createIfEmpty: true`.
2. For each new receipt: `navigate` to the thread `viewUrl`, then `find` "Download attachment <filename>", then `left_click` that ref, then wait 4s.
3. Move the file with `mv ~/Downloads/<filename> receipts/`. If Chrome renamed it (`... (1).PDF`), move it under the original filename.
4. Close the tab you created when you're done.

## 3. Rebuild, commit, deploy

```
bash .claude/skills/refresh-dashboard/publish.sh
```

The script runs `extract.py` and aborts if the full loan account number appears anywhere it would be published. It then commits **only** `data.json` (author NSP, no AI co-author trailer), pushes, waits for the Pages build, and checks the live `data.json`.

- If it prints `ABORT`, stop and tell the user. Do not work around it.
- If `extract.py` fails on a new PDF, the SCB layout may have changed. Dump that PDF's text the way `extract.py` does and adjust the regexes in `parse_receipt`.
- If the password fails, the user needs to fix `.env`. Never print or ask for the password in chat.

## 4. Report

Tell the user the months added, the new balance, the total principal and interest paid so far, the commit hash, and the site URL: https://natchaphon-gamedev.github.io/family-utilities/

Also mention any other uncommitted changes from `git status`. The script leaves them alone.
