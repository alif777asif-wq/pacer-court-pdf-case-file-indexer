"""Text extraction: poppler text layer first, Tesseract OCR for pages that have no usable text layer."""
from __future__ import annotations

import hashlib
import io
import logging
import re
import subprocess
from dataclasses import dataclass, field

LOG = logging.getLogger("courtfile.extract")

# A page whose text layer holds fewer characters than this (after removing the ECF header stamp) is
# treated as a scanned image and sent to OCR.
MIN_BODY_CHARS = 60
OCR_DPI = 200

PII_PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "phone": re.compile(r"(?<!\d)(?:\(\d{3}\)\s?|\d{3}[-.\s])\d{3}[-.\s]\d{4}(?!\d)"),
    "ssn_like": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "street_zip": re.compile(r"\b[A-Z]{2}\s\d{5}(?:-\d{4})?\b"),
}
_STAMP_LINE = re.compile(r"^\s*(?:Appellate\s+)?(?:Case|Appeal)\b.*$", re.M)


@dataclass
class PdfText:
    path: str
    sha256: str
    size_bytes: int
    pages: list[str]
    ocr_pages: list[int] = field(default_factory=list)
    ocr_seconds: float = 0.0

    @property
    def n_pages(self) -> int:
        return len(self.pages)

    @property
    def text(self) -> str:
        return "\n\f".join(self.pages)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def poppler_pages(path: str) -> list[str]:
    out = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, check=True).stdout
    pages = out.decode("utf-8", "replace").split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    return pages


def pdfminer_pages(path: str) -> list[str]:
    """Second, independent extractor used only to cross-check the first."""
    from pdfminer.high_level import extract_text
    return extract_text(path).split("\f")


def body_chars(page_text: str) -> int:
    return len(re.sub(r"\s+", "", _STAMP_LINE.sub("", page_text)))


def ocr_page(path: str, index: int) -> str:
    import pypdfium2 as pdfium
    import pytesseract
    pdf = pdfium.PdfDocument(path)
    try:
        image = pdf[index].render(scale=OCR_DPI / 72).to_pil()
        return pytesseract.image_to_string(image)
    finally:
        pdf.close()


def read_pdf(path: str, ocr: bool = True) -> PdfText:
    import time
    pages = poppler_pages(path)
    doc = PdfText(path=path, sha256=sha256_file(path), size_bytes=__import__("os").path.getsize(path), pages=pages)
    if ocr:
        for i, page in enumerate(pages):
            if body_chars(page) < MIN_BODY_CHARS:
                t0 = time.perf_counter()
                ocr_text = ocr_page(path, i)
                doc.ocr_seconds += time.perf_counter() - t0
                if body_chars(ocr_text) > body_chars(page):
                    doc.pages[i] = page.rstrip() + "\n" + ocr_text
                    doc.ocr_pages.append(i + 1)
                    LOG.info("ocr %s page %d: %d chars recovered", path, i + 1, body_chars(ocr_text))
    return doc


def pii_counts(text: str) -> dict[str, int]:
    return {name: len(rx.findall(text)) for name, rx in PII_PATTERNS.items()}
