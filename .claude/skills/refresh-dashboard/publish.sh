#!/usr/bin/env bash
# Rebuild data.json from receipts/, check for leaks, commit data.json only, push, wait for GitHub Pages.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

REPO=Natchaphon-GameDev/family-utilities
SITE=https://natchaphon-gamedev.github.io/family-utilities/

.venv/bin/python extract.py

# The full loan account number is in the receipt filenames (MG-<account>-...). It must never be published.
account=$(ls receipts | grep -oE '^MG-[0-9]+' | head -1 | cut -c4-)
if [ -n "$account" ] && git grep -q "$account" -- . ':!receipts' ':!contract'; then
  echo "ABORT: full account number found in tracked files:"; git grep -l "$account"; exit 1
fi
if [ -n "$account" ] && grep -q "$account" data.json; then
  echo "ABORT: full account number found in data.json"; exit 1
fi

if git diff --quiet -- data.json; then
  echo "data.json unchanged; nothing to publish."; exit 0
fi

summary=$(.venv/bin/python -c '
import json; d = json.load(open("data.json")); r = d["receipts"]; last = r[-1]
print(last["month"], len(r), f"{last[\"balance\"]:,.2f}", f"{sum(x[\"principal\"] for x in r):,.2f}", f"{sum(x[\"interest\"] for x in r):,.2f}")')
read -r month count balance principal interest <<< "$summary"

git add data.json
git commit -q -F - <<EOF
Update loan data through $month

- data.json: $count receipt(s), latest $month; balance ฿$balance, principal paid ฿$principal, interest paid ฿$interest
EOF
git push -q

for _ in $(seq 1 30); do
  status=$(gh api "repos/$REPO/pages/builds/latest" --jq .status 2>/dev/null || true)
  [ "$status" = built ] && break
  [ "$status" = errored ] && { echo "Pages build errored"; exit 1; }
  sleep 10
done
echo "Pages: $status"
curl -s "${SITE}data.json" | grep -q "\"$month\"" && echo "Live site has $month: $SITE" || echo "Live data.json not showing $month yet (CDN cache); check again in a minute."
