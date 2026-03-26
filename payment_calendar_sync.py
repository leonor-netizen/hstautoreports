#!/usr/bin/env python3
"""Extract payment entries from a PDF and create Google Calendar events.

Usage:
  python payment_calendar_sync.py --pdf /path/to/file.pdf --calendar-id primary

Optional:
  --create-docs to create one Google Doc per payment and attach its link in the event description.

Environment:
  GOOGLE_APPLICATION_CREDENTIALS should point to a service-account json key file
  with Calendar and (optional) Docs/Drive permissions enabled.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import re
from decimal import Decimal, InvalidOperation
from typing import Iterable, List, Optional

import pdfplumber
from dateutil import parser as date_parser
from googleapiclient.discovery import build


DATE_PATTERNS = [
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}\b", re.IGNORECASE),
]
AMOUNT_RE = re.compile(r"\$?\s?(-?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)")
STATUS_RE = re.compile(r"\b(paid|pending|overdue|failed|processing|completed|cancelled)\b", re.IGNORECASE)


@dataclasses.dataclass
class PaymentRecord:
    date: dt.date
    amount: Decimal
    status: str
    memo: str



def extract_text(pdf_path: str) -> str:
    parts: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            parts.append(page_text)
    return "\n".join(parts)



def parse_date_from_text(text: str) -> Optional[dt.date]:
    for pattern in DATE_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        try:
            return date_parser.parse(m.group(0), dayfirst=False).date()
        except (ValueError, TypeError):
            continue
    return None



def parse_amount_from_text(text: str) -> Optional[Decimal]:
    matches = AMOUNT_RE.findall(text)
    for raw in matches:
        raw = raw.replace(",", "").strip()
        try:
            return Decimal(raw)
        except InvalidOperation:
            continue
    return None



def parse_status_from_text(text: str) -> str:
    m = STATUS_RE.search(text)
    return (m.group(1).lower() if m else "unknown")



def extract_payment_records(text: str) -> list[PaymentRecord]:
    records: list[PaymentRecord] = []
    # Heuristic: many payment statements have one payment row per line.
    for line in text.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue

        line_lower = line_clean.lower()
        if "payment" not in line_lower and "invoice" not in line_lower and "$" not in line_clean:
            continue

        date = parse_date_from_text(line_clean)
        amount = parse_amount_from_text(line_clean)
        if not date or amount is None:
            continue

        status = parse_status_from_text(line_clean)
        records.append(PaymentRecord(date=date, amount=amount, status=status, memo=line_clean))

    # Deduplicate exact duplicates while preserving order.
    seen = set()
    unique: list[PaymentRecord] = []
    for r in records:
        key = (r.date.isoformat(), str(r.amount), r.status, r.memo)
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    return unique



def build_calendar_service():
    return build("calendar", "v3")



def build_docs_service():
    return build("docs", "v1")



def build_drive_service():
    return build("drive", "v3")



def create_google_doc_for_payment(record: PaymentRecord, docs_service, drive_service) -> str:
    title = f"Payment {record.date.isoformat()} ${record.amount}"
    body = (
        f"Payment Date: {record.date.isoformat()}\n"
        f"Amount: ${record.amount}\n"
        f"Status: {record.status}\n"
        f"Source: {record.memo}\n"
    )

    doc = docs_service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]

    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={
            "requests": [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": body,
                    }
                }
            ]
        },
    ).execute()

    meta = drive_service.files().get(fileId=doc_id, fields="webViewLink").execute()
    return meta["webViewLink"]



def upsert_calendar_event(calendar_service, calendar_id: str, record: PaymentRecord, doc_link: str | None = None):
    start_date = record.date.isoformat()
    end_date = (record.date + dt.timedelta(days=1)).isoformat()

    description = (
        f"Payment amount: ${record.amount}\n"
        f"Status: {record.status}\n"
        f"Extracted row: {record.memo}\n"
    )
    if doc_link:
        description += f"Google Doc: {doc_link}\n"

    event_body = {
        "summary": f"Payment ${record.amount} ({record.status})",
        "description": description,
        "start": {"date": start_date},
        "end": {"date": end_date},
    }
    return calendar_service.events().insert(calendarId=calendar_id, body=event_body).execute()



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="Path to PDF with payment rows")
    parser.add_argument("--calendar-id", default="primary", help="Google Calendar ID")
    parser.add_argument("--create-docs", action="store_true", help="Create a Google Doc and link in event description")
    parser.add_argument("--dry-run", action="store_true", help="Print extracted data only")
    args = parser.parse_args()

    text = extract_text(args.pdf)
    records = extract_payment_records(text)

    if not records:
        raise SystemExit("No payment records detected. Try refining parser rules for your PDF format.")

    if args.dry_run:
        print(json.dumps([dataclasses.asdict(r) for r in records], default=str, indent=2))
        return

    calendar_service = build_calendar_service()
    docs_service = drive_service = None

    if args.create_docs:
        docs_service = build_docs_service()
        drive_service = build_drive_service()

    for record in records:
        link = None
        if args.create_docs and docs_service and drive_service:
            link = create_google_doc_for_payment(record, docs_service, drive_service)

        event = upsert_calendar_event(
            calendar_service=calendar_service,
            calendar_id=args.calendar_id,
            record=record,
            doc_link=link,
        )
        print(f"Created event: {event.get('htmlLink')}")


if __name__ == "__main__":
    main()
