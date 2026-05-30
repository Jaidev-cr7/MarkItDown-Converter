"""
app.py – LLM Markdown Converter
A Streamlit application that converts documents to Markdown using
Microsoft MarkItDown, with preview, stats, and download capabilities.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from utils.converter import ConversionResult, FileConverter
from utils.token_counter import count_chars, count_words, estimate_tokens, format_stat
from utils.zip_handler import build_zip_from_strings

# ---------------------------------------------------------------------------
# Paths (relative to this file so the app works from any working directory)
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
CONVERTED_DIR = BASE_DIR / "converted"

UPLOAD_DIR.mkdir(exist_ok=True)
CONVERTED_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="LLM Markdown Converter",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    /* ── Google Font ───────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Base / Background ─────────────────────────────────────────────── */
    .stApp {
        background: linear-gradient(135deg, #0d0d1a 0%, #111128 50%, #0a0a18 100%);
        color: #e2e8f0;
    }

    /* ── Sidebar ───────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: rgba(15, 15, 35, 0.95) !important;
        border-right: 1px solid rgba(99, 102, 241, 0.2);
    }

    /* ── Hero header ───────────────────────────────────────────────────── */
    .hero-header {
        text-align: center;
        padding: 2rem 0 1rem;
    }
    .hero-header h1 {
        font-size: 2.6rem;
        font-weight: 700;
        background: linear-gradient(90deg, #818cf8, #c084fc, #38bdf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.3rem;
    }
    .hero-header p {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 0;
    }

    /* ── Stat cards ────────────────────────────────────────────────────── */
    .stat-card {
        background: rgba(99, 102, 241, 0.08);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        text-align: center;
        transition: border-color 0.2s;
    }
    .stat-card:hover { border-color: rgba(99, 102, 241, 0.55); }
    .stat-card .label {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        color: #94a3b8;
        text-transform: uppercase;
    }
    .stat-card .value {
        font-size: 1.55rem;
        font-weight: 700;
        color: #a5b4fc;
        margin-top: 0.15rem;
    }

    /* ── File result card ──────────────────────────────────────────────── */
    .file-card {
        background: rgba(17, 17, 40, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
        transition: box-shadow 0.2s, border-color 0.2s;
    }
    .file-card:hover {
        box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.4);
        border-color: rgba(99, 102, 241, 0.4);
    }
    .file-card.success { border-left: 4px solid #34d399; }
    .file-card.error   { border-left: 4px solid #f87171; }

    .file-name {
        font-weight: 600;
        font-size: 1rem;
        color: #e2e8f0;
        margin-bottom: 0.3rem;
    }
    .badge {
        display: inline-block;
        border-radius: 20px;
        padding: 0.15rem 0.65rem;
        font-size: 0.72rem;
        font-weight: 600;
    }
    .badge-success { background: rgba(52, 211, 153, 0.15); color: #34d399; }
    .badge-error   { background: rgba(248, 113, 113, 0.15); color: #f87171; }
    .badge-info    { background: rgba(56, 189, 248, 0.15);  color: #38bdf8; }

    /* ── Markdown preview area ─────────────────────────────────────────── */
    .preview-box {
        background: rgba(10, 10, 25, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        max-height: 520px;
        overflow-y: auto;
        font-size: 0.9rem;
        line-height: 1.7;
        color: #cbd5e1;
    }

    /* ── History list ──────────────────────────────────────────────────── */
    .history-item {
        border-bottom: 1px solid rgba(99, 102, 241, 0.1);
        padding: 0.5rem 0;
        font-size: 0.85rem;
        color: #94a3b8;
    }
    .history-item span.ok   { color: #34d399; font-weight: 600; }
    .history-item span.fail { color: #f87171; font-weight: 600; }

    /* ── Upload section label ──────────────────────────────────────────── */
    .section-title {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #7c7f9e;
        margin-bottom: 0.6rem;
    }

    /* ── Scrollbar ─────────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(99, 102, 241, 0.4); border-radius: 3px; }

    /* ── Streamlit element overrides ───────────────────────────────────── */
    div[data-testid="stFileUploader"] {
        border: 2px dashed rgba(99, 102, 241, 0.4) !important;
        border-radius: 14px !important;
        padding: 1.5rem !important;
        background: rgba(99, 102, 241, 0.04) !important;
        transition: border-color 0.2s;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: rgba(99, 102, 241, 0.7) !important;
    }

    div[data-testid="stExpander"] {
        background: rgba(17, 17, 40, 0.6) !important;
        border: 1px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 10px !important;
    }

    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.18s ease !important;
    }
    .stButton > button:hover { transform: translateY(-1px); }

    /* Progress bar colour */
    div[data-testid="stProgressBar"] > div {
        background: linear-gradient(90deg, #818cf8, #c084fc) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

def _init_state() -> None:
    defaults: dict[str, Any] = {
        "results": [],          # list[ConversionResult] for current batch
        "history": [],          # list[dict] – lightweight session history
        "preview_index": None,  # which result is being previewed
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_state()

# ---------------------------------------------------------------------------
# Converter singleton (cached per session)
# ---------------------------------------------------------------------------

@st.cache_resource
def get_converter() -> FileConverter:
    return FileConverter(upload_dir=UPLOAD_DIR, converted_dir=CONVERTED_DIR)


converter = get_converter()

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _human_size(num_bytes: int) -> str:
    """Return a human-readable file size string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(num_bytes) < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024  # type: ignore[assignment]
    return f"{num_bytes:.1f} TB"


def _append_history(result: ConversionResult) -> None:
    st.session_state.history.append(
        {
            "filename": result.source_name,
            "status": "✅ OK" if result.success else "❌ Failed",
            "tokens": result.token_estimate,
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        }
    )


def _clear_all() -> None:
    """Remove all session results and their files from disk."""
    paths = [r.source_path for r in st.session_state.results]
    converter.cleanup_session_files(paths)
    st.session_state.results = []
    st.session_state.preview_index = None


def _render_stat_cards(result: ConversionResult) -> None:
    c1, c2, c3, c4 = st.columns(4)
    stats = [
        ("File Size",   _human_size(result.file_size_bytes)),
        ("Characters",  format_stat(result.char_count)),
        ("Words",       format_stat(result.word_count)),
        ("~Tokens",     format_stat(result.token_estimate)),
    ]
    for col, (label, value) in zip([c1, c2, c3, c4], stats):
        col.markdown(
            f"""
            <div class="stat-card">
                <div class="label">{label}</div>
                <div class="value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center;padding:1rem 0 1.5rem;">
            <div style="font-size:2.4rem;">⚡</div>
            <div style="font-size:1.1rem;font-weight:700;color:#a5b4fc;">LLM Markdown</div>
            <div style="font-size:0.75rem;color:#64748b;">Converter</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Supported formats</div>', unsafe_allow_html=True)
    formats_cols = st.columns(2)
    left_fmts = ["PDF", "DOCX / DOC", "PPTX / PPT", "XLSX / XLS", "CSV"]
    right_fmts = ["HTML / HTM", "TXT / MD", "JSON / XML", "Images (OCR)", "EPUB"]
    for col, fmts in zip(formats_cols, [left_fmts, right_fmts]):
        for f in fmts:
            col.markdown(f"<small>• {f}</small>", unsafe_allow_html=True)

    st.divider()

    # Session summary
    results: list[ConversionResult] = st.session_state.results
    n_ok   = sum(1 for r in results if r.success)
    n_fail = sum(1 for r in results if not r.success)

    st.markdown('<div class="section-title">Session summary</div>', unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    m1.metric("Converted", n_ok)
    m2.metric("Failed", n_fail)

    if results:
        total_tokens = sum(r.token_estimate for r in results if r.success)
        st.markdown(f"<small>Total ~tokens: **{format_stat(total_tokens)}**</small>", unsafe_allow_html=True)

    st.divider()

    # Session history
    st.markdown('<div class="section-title">History</div>', unsafe_allow_html=True)
    history: list[dict] = st.session_state.history
    if not history:
        st.caption("No conversions yet.")
    else:
        for entry in reversed(history[-20:]):  # show latest 20
            status_cls = "ok" if "OK" in entry["status"] else "fail"
            st.markdown(
                f"""<div class="history-item">
                    {entry['timestamp']} &nbsp;
                    <span class="{status_cls}">{entry['status']}</span>
                    &nbsp;{entry['filename']}
                    &nbsp;<span style="color:#7c7f9e">~{format_stat(entry['tokens'])} tok</span>
                </div>""",
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

# Hero header
st.markdown(
    """
    <div class="hero-header">
        <h1>⚡ LLM Markdown Converter</h1>
        <p>Convert any document to clean Markdown — ready for ChatGPT, Claude, Gemini, NotebookLM & more.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ── Upload ──────────────────────────────────────────────────────────────────

st.markdown('<div class="section-title">📂 Upload files</div>', unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    label="Drag & drop files here, or click to browse",
    accept_multiple_files=True,
    help="Supports PDF, DOCX, PPTX, XLSX, TXT, HTML, CSV, JSON, XML, images, EPUB, and more.",
    label_visibility="visible",
)

col_convert, col_clear = st.columns([2, 1])

with col_convert:
    convert_btn = st.button(
        "🚀 Convert to Markdown",
        type="primary",
        use_container_width=True,
        disabled=not uploaded_files,
    )

with col_clear:
    clear_btn = st.button(
        "🗑️ Clear All",
        use_container_width=True,
        disabled=not st.session_state.results,
    )

if clear_btn:
    _clear_all()
    st.rerun()

# ── Conversion ──────────────────────────────────────────────────────────────

if convert_btn and uploaded_files:
    st.session_state.results = []
    st.session_state.preview_index = None

    progress_bar = st.progress(0, text="Preparing…")
    status_area  = st.empty()
    total        = len(uploaded_files)

    new_results: list[ConversionResult] = []

    for idx, uf in enumerate(uploaded_files):
        status_area.info(f"Converting **{uf.name}** ({idx + 1}/{total})…")
        progress_bar.progress((idx) / total, text=f"{idx}/{total} files processed")

        # Validate extension
        if not converter.is_supported(uf.name):
            result = ConversionResult(
                source_path=UPLOAD_DIR / uf.name,
                success=False,
                error=f"Extension '{Path(uf.name).suffix}' is not in the supported list.",
                file_size_bytes=len(uf.getvalue()),
            )
            new_results.append(result)
            _append_history(result)
            continue

        # Save to disk then convert
        try:
            saved_path = converter.save_upload(uf.name, uf.getvalue())
            result = converter.convert(saved_path)
        except Exception as exc:  # noqa: BLE001
            result = ConversionResult(
                source_path=UPLOAD_DIR / uf.name,
                success=False,
                error=str(exc),
                file_size_bytes=len(uf.getvalue()),
            )

        new_results.append(result)
        _append_history(result)

    progress_bar.progress(1.0, text="Done!")
    status_area.empty()

    st.session_state.results = new_results

    ok_count   = sum(1 for r in new_results if r.success)
    fail_count = total - ok_count
    if ok_count:
        st.success(f"✅ Converted {ok_count}/{total} file(s) successfully.")
    if fail_count:
        st.error(f"❌ {fail_count} file(s) failed — see details below.")

# ── Results ─────────────────────────────────────────────────────────────────

results: list[ConversionResult] = st.session_state.results

if results:
    st.divider()
    st.markdown('<div class="section-title">📄 Conversion results</div>', unsafe_allow_html=True)

    # ── Bulk download (all as ZIP) ──────────────────────────────────────
    successful = [r for r in results if r.success]
    if len(successful) > 1:
        zip_items = [(r.source_path.stem + ".md", r.markdown) for r in successful]
        zip_bytes = build_zip_from_strings(zip_items)
        st.download_button(
            label=f"📦 Download all {len(successful)} files as ZIP",
            data=zip_bytes,
            file_name="converted_markdown.zip",
            mime="application/zip",
            use_container_width=True,
        )
        st.markdown("")

    # ── Per-file cards ─────────────────────────────────────────────────
    for i, result in enumerate(results):
        card_class = "success" if result.success else "error"
        status_badge = (
            '<span class="badge badge-success">✅ Converted</span>'
            if result.success
            else '<span class="badge badge-error">❌ Failed</span>'
        )
        size_badge = f'<span class="badge badge-info">{_human_size(result.file_size_bytes)}</span>'
        duration_badge = f'<span class="badge badge-info">{result.duration_s:.2f}s</span>'

        st.markdown(
            f"""
            <div class="file-card {card_class}">
                <div class="file-name">📄 {result.source_name}</div>
                <div style="margin-top:0.4rem;">
                    {status_badge}&nbsp;{size_badge}&nbsp;{duration_badge}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if result.success:
            _render_stat_cards(result)
            st.markdown("")

            col_prev, col_dl = st.columns([3, 1])

            with col_prev:
                if st.button(
                    f"👁️ Preview Markdown",
                    key=f"preview_{i}",
                    use_container_width=True,
                ):
                    st.session_state.preview_index = (
                        None if st.session_state.preview_index == i else i
                    )

            with col_dl:
                st.download_button(
                    label="⬇️ Download .md",
                    data=result.markdown.encode("utf-8"),
                    file_name=result.source_path.stem + ".md",
                    mime="text/markdown",
                    key=f"dl_{i}",
                    use_container_width=True,
                )

            # Inline markdown preview (toggled)
            if st.session_state.preview_index == i:
                st.markdown("")
                tab_rendered, tab_raw = st.tabs(["🖥️ Rendered", "📝 Raw Markdown"])

                with tab_rendered:
                    st.markdown(result.markdown, unsafe_allow_html=False)

                with tab_raw:
                    st.markdown(
                        f'<div class="preview-box"><pre style="white-space:pre-wrap;word-break:break-word;">{result.markdown[:8000]}'
                        + ("…\n*(truncated to 8 000 chars for display)*" if len(result.markdown) > 8000 else "")
                        + "</pre></div>",
                        unsafe_allow_html=True,
                    )

        else:
            # Show error details in an expander
            with st.expander("⚠️ Error details"):
                st.error(result.error)

        st.markdown("---")

# ── Empty state ──────────────────────────────────────────────────────────────

if not results and not uploaded_files:
    st.markdown(
        """
        <div style="text-align:center;padding:3rem 1rem;color:#4b5563;">
            <div style="font-size:3.5rem;margin-bottom:0.8rem;">📂</div>
            <div style="font-size:1.1rem;font-weight:600;color:#6b7280;">No files uploaded yet</div>
            <div style="font-size:0.85rem;margin-top:0.4rem;">
                Drag &amp; drop files above, or click to browse your computer.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
