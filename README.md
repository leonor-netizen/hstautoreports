## Payment PDF → Google Calendar sync

This workspace now includes `payment_calendar_sync.py`, a CLI tool that:

1. Extracts likely payment lines from a PDF.
2. Parses payment date, amount, and status.
3. Creates calendar events in your Google Calendar.
4. Optionally creates a Google Doc per payment and adds the doc link to the event description.

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a Google Cloud project and enable APIs:
- Google Calendar API
- Google Docs API (if using `--create-docs`)
- Google Drive API (if using `--create-docs`)

Then export credentials:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/service-account.json"
```

### Usage

Preview extraction without creating calendar events:

```bash
python payment_calendar_sync.py --pdf /path/to/payments.pdf --dry-run
```

Create events on your primary calendar:

```bash
python payment_calendar_sync.py --pdf /path/to/payments.pdf --calendar-id primary
```

Create events and a Google Doc per event:

```bash
python payment_calendar_sync.py --pdf /path/to/payments.pdf --calendar-id primary --create-docs
```

### Notes

- PDF formats vary a lot. You may need to tweak regexes in `extract_payment_records` for your exact statement/invoice format.
- Service accounts need access to the target calendar and drive files, or use user OAuth flow if preferred.
