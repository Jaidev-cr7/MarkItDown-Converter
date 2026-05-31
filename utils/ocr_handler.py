"""
ocr_handler.py – OCR fallback for images and scanned PDFs.

Strategy:
  1. Try normal MarkItDown conversion first (caller's responsibility).
  2. If the result is empty / too short / PDF appears image-based, the
     caller invokes ``run_ocr(path)`` to get text via EasyOCR.

Dependencies (optional – gracefully degraded if absent):
  - easyocr
  - Pillow
  - pdf2image  (+ poppler on PATH)

Changes vs original:
  - DPI raised from 200 → 300 for better small-font accuracy.
  - EasyOCR called with paragraph=False to preserve reading order on
    multi-column layouts; lines are joined with a single newline.
  - Streamlit Community Cloud compatible — no Tesseract binary required.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Availability flags
# ---------------------------------------------------------------------------

try:
    import easyocr  # type: ignore
    _EASYOCR_OK = True
except ImportError:
    _EASYOCR_OK = False

try:
    from PIL import Image  # type: ignore
    import numpy as np  # type: ignore
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

try:
    from pdf2image import convert_from_path  # type: ignore
    _PDF2IMAGE_OK = True
except ImportError:
    _PDF2IMAGE_OK = False


# ---------------------------------------------------------------------------
# EasyOCR reader – lazily initialised singleton
# ---------------------------------------------------------------------------

_reader: "easyocr.Reader | None" = None  # type: ignore[name-defined]


def _get_reader() -> "easyocr.Reader":  # type: ignore[name-defined]
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

OCR_AVAILABLE: bool = _EASYOCR_OK and _PIL_OK

# Minimum characters below which we consider MarkItDown output "empty"
_MIN_MEANINGFUL_CHARS: int = 80

IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
)

# DPI for PDF → image rendering. 300 is the document-OCR standard;
# 200 was borderline for small fonts and fine detail.
_PDF_RENDER_DPI: int = 300


def ocr_available() -> bool:
    return OCR_AVAILABLE


def pdf_ocr_available() -> bool:
    return OCR_AVAILABLE and _PDF2IMAGE_OK


def needs_ocr_fallback(text: str, source_path: Path) -> bool:
    """Decide whether OCR fallback should be attempted."""
    suffix = source_path.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return True
    if len(text.strip()) < _MIN_MEANINGFUL_CHARS:
        return True
    return False


def run_ocr(source_path: Path) -> tuple[str, str]:
    """Run OCR on *source_path* and return (ocr_text, warning_message)."""
    if not OCR_AVAILABLE:
        return "", "easyocr / Pillow not installed – OCR unavailable."

    suffix = source_path.suffix.lower()

    try:
        if suffix == ".pdf":
            return _ocr_pdf(source_path)
        elif suffix in IMAGE_EXTENSIONS:
            return _ocr_image(source_path)
        else:
            return "", f"OCR not supported for '{suffix}' files."
    except Exception as exc:  # noqa: BLE001
        logger.exception("OCR failed for %s", source_path)
        return "", f"OCR error: {exc}"


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _run_easyocr_on_image(img: "Image.Image") -> str:  # type: ignore[name-defined]
    """Run EasyOCR on a PIL Image and return the joined text.

    Uses paragraph=False (detail=0) so EasyOCR returns individual text lines
    in their natural detected order rather than grouping them — this produces
    better results on multi-column documents where paragraph grouping can mix
    columns together.
    """
    img_array = np.array(img.convert("RGB"))
    reader = _get_reader()
    # detail=0 → plain strings, paragraph=False → preserve per-line order
    results = reader.readtext(img_array, detail=0, paragraph=False)
    return "\n".join(results).strip()


def _ocr_image(path: Path) -> tuple[str, str]:
    if not _PIL_OK:
        return "", "Pillow not installed."
    img = Image.open(path)
    text = _run_easyocr_on_image(img)
    return text, ""


def _ocr_pdf(path: Path) -> tuple[str, str]:
    """OCR a PDF by rendering each page to an image then running EasyOCR."""
    if not _PDF2IMAGE_OK:
        return "", (
            "pdf2image not installed (or poppler missing from PATH). "
            "Install with: pip install pdf2image"
        )

    # 300 DPI: standard for document OCR; catches small fonts that 200 DPI misses
    pages = convert_from_path(str(path), dpi=_PDF_RENDER_DPI)
    parts: list[str] = []
    for i, page_img in enumerate(pages, start=1):
        page_text = _run_easyocr_on_image(page_img)
        if page_text:
            parts.append(f"<!-- Page {i} -->\n{page_text}")

    return "\n\n".join(parts), ""