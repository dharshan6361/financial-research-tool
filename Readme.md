# Financial Statement Extraction Tool

I built this as a small research tool that extracts income-statement line items and numeric values from financial PDF reports and converts them into a structured CSV file for analysis.

It is designed as a task-specific research utility, not a chatbot.

## What it does

- Upload a financial PDF
- Extract page text
- Uses OCR fallback for scanned pages
- Detects revenue / expense / profit / tax lines
- Extracts numeric values directly (no guessing)
- Adds page and source text for traceability
- Exports structured CSV

## Approach

I used deterministic parsing first to avoid hallucinated financial numbers. The tool only captures visible numeric values and keeps the source line so results can be verified. The design allows an AI layer to be added later for normalization if required.

## Run locally

Install:

pip install -r requirements.txt

Run:

python -m streamlit run app.py

## Notes

- OCR requires Tesseract and Poppler installed locally
- Works best on text PDFs
- Scanned tables may have partial structure
- First ~12 pages processed for speed

This was built as part of a research platform assignment focused on reliability and structured outputs.
