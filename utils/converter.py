"""
converter.py – Wraps Microsoft MarkItDown and manages file-level conversion.

Security improvements (Priority 6):
  - UUID-based internal filenames prevent collisions & path traversal.
  - ``save_upload`` now returns a UUID-named path; original name is stored separately.
  - ``cleanup_session_files`` robustly removes both upload and converted artefacts.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from markitdown import MarkItDown


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ConversionResult:
    """Holds the outcome of a single file conversion."""

    source_path: Path           # UUID-named path on disk
    source_name: str = ""       # original user-visible filename
    output_path: Optional[Path] = None
    markdown: str = ""
    success: bool = False
    error: str = ""
    duration_s: float = 0.0
    file_size_bytes: int = 0

    # OCR metadata
    ocr_used: bool = False
    ocr_warning: str = ""

    # Derived stats (populated after conversion)
    char_count: int = field(default=0, init=False)
    word_count: int = field(default=0, init=False)
    token_estimate: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        # Back-fill source_name from path if not provided
        if not self.source_name:
            self.source_name = self.source_path.name
        self._compute_stats()

    def _compute_stats(self) -> None:
        self.char_count = len(self.markdown)
        self.word_count = len(self.markdown.split()) if self.markdown else 0
        self.token_estimate = self.char_count // 4  # rough GPT-style estimate


# ---------------------------------------------------------------------------
# Converter class
# ---------------------------------------------------------------------------

class FileConverter:
    """Thin wrapper around MarkItDown that adds path management and error handling."""

    # All extensions officially tested / supported by MarkItDown
    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
        {
            ".pdf", ".docx", ".doc", ".pptx", ".ppt",
            ".xlsx", ".xls", ".csv",
            ".html", ".htm",
            ".txt", ".md", ".rst",
            ".json", ".xml",
            ".zip",            # MarkItDown can recurse into zip archives
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
            ".mp3", ".wav", ".ogg",
            ".epub",
        }
    )

    def __init__(self, upload_dir: Path, converted_dir: Path) -> None:
        self.upload_dir = upload_dir
        self.converted_dir = converted_dir
        self._md = MarkItDown()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def convert(self, source_path: Path, original_name: str = "") -> ConversionResult:
        """Convert *source_path* to Markdown and write the .md file.

        Returns a :class:`ConversionResult` regardless of success/failure.
        """
        display_name = original_name or source_path.name
        result = ConversionResult(
            source_path=source_path,
            source_name=display_name,
            file_size_bytes=source_path.stat().st_size if source_path.exists() else 0,
        )

        start = time.perf_counter()
        try:
            md_result = self._md.convert(str(source_path))
            markdown_text: str = md_result.text_content or ""

            output_path = self._output_path(source_path)
            output_path.write_text(markdown_text, encoding="utf-8")

            result.markdown = markdown_text
            result.output_path = output_path
            result.success = True
        except Exception as exc:  # noqa: BLE001
            result.error = str(exc)
            result.success = False
        finally:
            result.duration_s = time.perf_counter() - start
            result._compute_stats()

        return result

    def save_upload(self, filename: str, data: bytes) -> tuple[Path, str]:
        """Persist raw upload bytes to the uploads directory with a UUID filename.

        Returns:
            (uuid_path, original_name) – uuid_path is the on-disk location;
            original_name is the user's original filename (sanitised stem + suffix).
        """
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(filename).suffix.lower()
        unique_name = f"{uuid.uuid4().hex}{suffix}"
        dest = self.upload_dir / unique_name
        dest.write_bytes(data)
        return dest, filename

    def is_supported(self, filename: str) -> bool:
        return Path(filename).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def cleanup_session_files(
        self, paths: list[Path], *, remove_converted: bool = True
    ) -> None:
        """Delete a list of uploaded / converted files from disk."""
        for p in paths:
            if p and p.exists():
                try:
                    p.unlink(missing_ok=True)
                except OSError:
                    pass
        if remove_converted:
            converted_stem_map = {
                p.stem: p for p in self.converted_dir.glob("*.md")
            }
            for path in paths:
                md_path = converted_stem_map.get(path.stem)
                if md_path and md_path.exists():
                    try:
                        md_path.unlink(missing_ok=True)
                    except OSError:
                        pass

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _output_path(self, source_path: Path) -> Path:
        """Derive an output .md path from the UUID source filename."""
        self.converted_dir.mkdir(parents=True, exist_ok=True)
        return self.converted_dir / (source_path.stem + ".md")
