## Google Sheet PDF Auto-Export

This repository now auto-generates a PDF from this Google Sheet tab:

- `https://docs.google.com/spreadsheets/d/13yiIiIXnokkZtE0q3aGOv6RPaRo_WL3EAvd-gJ4DIgA/edit?gid=1038490019#gid=1038490019`

### Automatic generation (GitHub Actions)

The workflow `.github/workflows/generate-sheet-pdf.yml` runs:

- on demand (`workflow_dispatch`)
- daily at `12:00 UTC`

It generates `output/sheet-report.pdf`, commits updates, and uploads the file as an artifact.

### Manual generation

Run:

```bash
python scripts/export_sheet_pdf.py \
  "https://docs.google.com/spreadsheets/d/13yiIiIXnokkZtE0q3aGOv6RPaRo_WL3EAvd-gJ4DIgA/edit?gid=1038490019#gid=1038490019" \
  --output output/sheet-report.pdf
```

If the sheet is not publicly accessible, Google may return HTML instead of a PDF.
