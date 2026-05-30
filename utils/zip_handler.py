"""
zip_handler.py – Bundles multiple converted Markdown files into a single ZIP.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Sequence


def build_zip(md_paths: Sequence[Path]) -> bytes:
    """Create an in-memory ZIP archive containing every path in *md_paths*.

    Returns the raw ZIP bytes ready to be passed to ``st.download_button``.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in md_paths:
            if path.exists():
                zf.write(path, arcname=path.name)
    buffer.seek(0)
    return buffer.read()


def build_zip_from_strings(items: Sequence[tuple[str, str]]) -> bytes:
    """Create a ZIP from (filename, content) string pairs.

    Useful when the caller has the Markdown text in memory but the file
    might not have been written to disk yet.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename, content in items:
            zf.writestr(filename, content.encode("utf-8"))
    buffer.seek(0)
    return buffer.read()
