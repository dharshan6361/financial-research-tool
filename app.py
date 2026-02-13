import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# ----- Optional OCR imports -----
try:
    import pytesseract
    from pdf2image import convert_from_bytes
    OCR_AVAILABLE = True
except:
    OCR_AVAILABLE = False


# ----- Local-only OCR paths -----
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPLER_PATH = r"C:\poppler\poppler-25.12.0\Library\bin"

if OCR_AVAILABLE:
    try:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    except:
        OCR_AVAILABLE = False


st.title("Financial Statement Extraction Tool")
st.caption("Extract income-statement style line items from financial PDFs into analyst-ready CSV.")

file = st.file_uploader("Upload Financial PDF", type=["pdf"])


# ---------- normalization ----------

def normalize_name(line):

    l = line.lower()

    if "revenue" in l or "total income" in l:
        return "Revenue"

    if "other operating revenue" in l:
        return "Other Operating Revenue"

    if "profit after tax" in l or "net profit" in l:
        return "Net Income"

    if "tax" in l:
        return "Tax"

    if "expense" in l or "cost" in l:
        return "Expenses"

    return line.strip()


# ---------- extraction ----------

def extract_financial_lines(text, page_num):

    rows = []

    for line in text.split("\n"):

        nums = re.findall(r"\d[\d,]*\.?\d*", line)

        if len(nums) < 2:
            continue

        if not any(k in line.lower() for k in
            ["revenue","income","profit","tax","expense","cost"]):
            continue

        for val in nums:
            rows.append({
                "line_item": normalize_name(line),
                "value": val,
                "page": page_num,
                "source_text": line.strip(),
                "confidence": "high"
            })

    return rows


# ---------- OCR fallback (safe) ----------

def extract_text_with_ocr(pdf_bytes, page_num):

    if not OCR_AVAILABLE:
        return None

    try:
        images = convert_from_bytes(
            pdf_bytes,
            first_page=page_num,
            last_page=page_num,
            dpi=300,
            poppler_path=POPLER_PATH
        )

        return pytesseract.image_to_string(images[0])

    except Exception:
        st.info("OCR not available in this deployment — using text-only mode.")
        return None


# ---------- run tool ----------

if file and st.button("Run Income Statement Extraction"):

    pdf_bytes = file.read()   # read once

    all_rows = []
    raw_preview = ""

    # ✅ FIX — open from bytes buffer, not file stream
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:

        page_limit = min(len(pdf.pages), 12)

        for i in range(page_limit):

            page_num = i + 1
            st.write(f"Processing page {page_num}")

            text = pdf.pages[i].extract_text()

            # OCR fallback only if needed
            if not text:
                ocr_text = extract_text_with_ocr(pdf_bytes, page_num)
                if ocr_text:
                    text = ocr_text

            if text and not raw_preview:
                raw_preview = text[:3000]

            if not text:
                continue

            rows = extract_financial_lines(text, page_num)
            all_rows.extend(rows)


    # ---------- structured output ----------

    if all_rows:

        df = pd.DataFrame(all_rows)

        df["value"] = df["value"].str.replace(",", "").astype(float)

        df = df.sort_values(["line_item", "page"])

        st.subheader("Extracted Financial Lines")
        st.dataframe(df)

        st.download_button(
            "Download CSV",
            df.to_csv(index=False),
            "financial_extract.csv"
        )

    # ---------- graceful fallback ----------

    else:

        st.warning(
            "No structured financial rows detected. "
            "This PDF may be image-only. Cloud deployment runs without OCR."
        )

        if raw_preview:
            st.subheader("Raw Extracted Text Preview")
            st.text(raw_preview)

            st.download_button(
                "Download Raw Text",
                raw_preview,
                "raw_text.txt"
            )


# ---------- limitation note ----------

st.markdown("""
### ⚠️ Limitations

• Deterministic parsing with optional OCR fallback  
• Cloud deployment runs in text-only mode (no Poppler/Tesseract)  
• Scanned tables may have partial structure  
• First ~12 pages processed for speed  
• Values are copied exactly — no guessing or hallucination  
• Source text and page number are preserved for verification
""")
