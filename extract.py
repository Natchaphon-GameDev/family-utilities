"""Decrypt SCB Home Loan receipt PDFs in receipts/ and write data.json for dashboard.html."""
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from pypdf import PdfReader

ROOT = Path(__file__).parent
NUM = r"([\d,]+\.\d{2})"


def money(s):
    return float(s.replace(",", ""))


def parse_receipt(path, password):
    reader = PdfReader(path)
    if reader.is_encrypted and not reader.decrypt(password):
        raise SystemExit(f"Wrong password for {path.name}")
    text = "\n".join(page.extract_text() for page in reader.pages)

    day, month, year = re.search(r"\(Date\)\s+(\d{2})/(\d{2})/(\d{4})", text).groups()
    rate = float(re.search(r"\(Interest Rate\)\s+([\d.]+)%", text).group(1))
    receipt_no = re.search(r"\(No\.\)\s+(\d+)", text).group(1)
    # After "บาท (Baht)": paid principal, paid interest, balance principal, balance interest.
    paid_principal, paid_interest, balance, balance_interest = map(
        money, re.search(r"\(Baht\)\s+" + r"\s+".join([NUM] * 4), text).groups()
    )
    total = money(re.search(r"\(Total\)\s+" + NUM, text).group(1))

    return {
        "month": f"{year}-{month}",
        "date": f"{year}-{month}-{day}",
        "no": receipt_no,
        "paid": total,
        "principal": paid_principal,
        "interest": paid_interest,
        # Default interest, insurance premium and fees; derived so any non-zero line is caught.
        "other": round(total - paid_principal - paid_interest, 2),
        "balance": balance,
        "balance_interest": balance_interest,
        "rate": rate,
    }


def main():
    load_dotenv(ROOT / ".env")
    password = os.environ["SCB_PDF_PASSWORD"]

    # Several receipts can share a month (SCB splits payments); keep each one, dedupe by receipt number.
    by_no = {}
    for path in sorted((ROOT / "receipts").glob("*.[pP][dD][fF]")):
        r = parse_receipt(path, password)
        by_no[r["no"]] = r
    receipts = sorted(by_no.values(), key=lambda r: (r["date"], r["no"]))

    contract = json.loads((ROOT / "contract.json").read_text())
    (ROOT / "data.json").write_text(
        json.dumps({"contract": contract, "receipts": receipts}, ensure_ascii=False, indent=2)
    )
    for r in receipts:
        print(f"{r['date']}  #{r['no'][-3:]}  paid {r['paid']:>12,.2f}  principal {r['principal']:>12,.2f}  "
              f"interest {r['interest']:>10,.2f}  balance {r['balance']:>14,.2f}  rate {r['rate']}%")
    print(f"{len(receipts)} receipt(s) -> data.json")


if __name__ == "__main__":
    main()
