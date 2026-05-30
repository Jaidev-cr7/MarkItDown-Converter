"""
converter.py – Wraps Microsoft MarkItDown and manages file-level conversion.
"""

from __future__ import annotations

import time
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

    source_path: Path
    output_path: Optional[Path] = None
    markdown: str = ""
    success: bool = False
    error: str = ""
    duration_s: float = 0.0
    file_size_bytes: int = 0

    # Derived stats (populated after conversion)
    char_count: int = field(default=0, init=False)
    word_count: int = field(default=0, init=False)
    token_estimate: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self._compute_stats()

    def _compute_stats(self) -> None:
        self.char_count = len(self.markdown)
        self.word_count = len(self.markdown.split()) if self.markdown else 0
        self.token_estimate = self.char_count // 4  # rough GPT-style estimate

    @property
    def source_name(self) -> str:
        return self.source_path.name


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
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",  # image OCR / description
            ".mp3", ".wav", ".ogg",                             # audio transcription (if configured)
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

    def convert(self, source_path: Path) -> ConversionResult:
        """Convert *source_path* to Markdown and write the .md file.

        Returns a :class:`ConversionResult` regardless of success/failure.
        """
        result = ConversionResult(
            source_path=source_path,
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

    def save_upload(self, filename: str, data: bytes) -> Path:
        """Persist raw upload bytes to the uploads directory.

        Returns the Path where the file was saved.
        """
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        dest = self.upload_dir / filename
        dest.write_bytes(data)
        return dest

    def is_supported(self, filename: str) -> bool:
        return Path(filename).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def cleanup_session_files(
        self, paths: list[Path], *, remove_converted: bool = True
    ) -> None:
        """Delete a list of uploaded / converted files from disk."""
        for p in paths:
            if p and p.exists():
                p.unlink(missing_ok=True)
        if remove_converted:
            converted_stem_map = {
                p.stem: p for p in self.converted_dir.glob("*.md")
            }
            for path in paths:
                md_path = converted_stem_map.get(path.stem)
                if md_path and md_path.exists():
                    md_path.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _output_path(self, source_path: Path) -> Path:
        """Derive an output .md path from the source filename."""
        self.converted_dir.mkdir(parents=True, exist_ok=True)
        return self.converted_dir / (source_path.stem + ".md")
