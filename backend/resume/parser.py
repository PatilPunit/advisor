"""
resume/parser.py
-----------------
Reads a PDF resume and extracts its raw text content.

Flow:
  open pdf (from raw bytes) -> for each page -> extract text -> join text
"""

import fitz  # PyMuPDF


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts and returns the full text content of a PDF given as raw bytes.

    Args:
        file_bytes: the raw content of a .pdf file (e.g. from an uploaded file)

    Returns:
        A single string containing text from every page, in order.

    Raises:
        ValueError: if the bytes can't be opened as a valid PDF.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Could not read PDF: {e}")

    pages_text = []
    for page in doc:
        pages_text.append(page.get_text())
    doc.close()

    full_text = "\n".join(pages_text)
    return full_text