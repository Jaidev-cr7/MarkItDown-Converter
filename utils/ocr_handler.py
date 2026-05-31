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

Streamlit Community Cloud compatible — no system binary (Tesseract) required.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Availability flags (import-time, so missing libs don't crash at start-up)
# ---------------------------------------------------------------------------

try:
    import easyocr  # type: ignore
    _EASYOCR_OK = True
except ImportError:
    _EASYOCR_OK = False

try:
    from PIL import Image  # type: ignore
    import numpy as np  # type: ignore  # easyocr works best with numpy arrays
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

try:
    from pdf2image import convert_from_path  # type: ignore
    _PDF2IMAGE_OK = True
except ImportError:
    _PDF2IMAGE_OK = False


# ---------------------------------------------------------------------------
# EasyOCR reader – lazily initialised singleton to avoid reloading models
# ---------------------------------------------------------------------------

_reader: "easyocr.Reader | None" = None  # type: ignore[name-defined]


def _get_reader() -> "easyocr.Reader":  # type: ignore[name-defined]
    """Return (and cache) the EasyOCR reader instance."""
    global _reader
    if _reader is None:
        # gpu=False ensures CPU-only inference; safe on all cloud environments
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

OCR_AVAILABLE: bool = _EASYOCR_OK and _PIL_OK


def ocr_available() -> bool:
    """Return True if easyocr + Pillow are both importable."""
    return OCR_AVAILABLE


def pdf_ocr_available() -> bool:
    """Return True if PDF OCR (pdf2image) is also available."""
    return OCR_AVAILABLE and _PDF2IMAGE_OK


# Minimum characters below which we consider MarkItDown output "empty"
_MIN_MEANINGFUL_CHARS: int = 80

# Image extensions that should go through OCR
IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
)


def needs_ocr_fallback(text: str, source_path: Path) -> bool:
    """Decide whether OCR fallback should be attempted.

    Returns True when:
    - The source is an image file, OR
    - The extracted text is absent / shorter than the minimum threshold.
    """
    suffix = source_path.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return True
    if len(text.strip()) < _MIN_MEANINGFUL_CHARS:
        return True
    return False


def run_ocr(source_path: Path) -> tuple[str, str]:
    """Run OCR on *source_path* and return (ocr_text, warning_message).

    For PDFs: converts pages to images via pdf2image then runs EasyOCR.
    For images: runs EasyOCR directly.

    Returns:
        (text, warning)  – warning is non-empty if something went wrong.
    """
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
    """Run EasyOCR on a PIL Image and return the joined text."""
    img_array = np.array(img.convert("RGB"))
    reader = _get_reader()
    results = reader.readtext(img_array, detail=0, paragraph=True)
    return "\n".join(results).strip()


def _ocr_image(path: Path) -> tuple[str, str]:
    """OCR a single image file."""
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

    pages = convert_from_path(str(path), dpi=200)
    parts: list[str] = []
    for i, page_img in enumerate(pages, start=1):
        page_text = _run_easyocr_on_image(page_img)
        if page_text:
            parts.append(f"<!-- Page {i} -->\n{page_text}")

    return "\n\n".join(parts), ""