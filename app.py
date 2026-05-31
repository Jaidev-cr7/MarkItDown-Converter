"""
app.py – MarkItDown Streamlit UI
Integrates OCR fallback, Markdown optimization, smart chunking, and copy features.
OCR and Optimization are always-on automatic.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from utils.converter import FileConverter
from utils.ocr_handler import ocr_available, needs_ocr_fallback, run_ocr
from utils.optimizer import optimize_markdown, OptimizationStats, chunk_markdown, CHUNK_PRESETS
from utils.token_counter import estimate_tokens, format_stat, TOKEN_BACKEND
from utils.zip_handler import build_zip, build_zip_from_strings

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="MarkItDown Converter",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------

UPLOAD_DIR = Path("tmp/uploads")
CONVERTED_DIR = Path("tmp/converted")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CONVERTED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

def _init_state() -> None:
    defaults = {
        "results": [],
        "history": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_state()

# ---------------------------------------------------------------------------
# Converter singleton
# ---------------------------------------------------------------------------

@st.cache_resource
def get_converter() -> FileConverter:
    return FileConverter(UPLOAD_DIR, CONVERTED_DIR)

converter = get_converter()

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Hero ── */
.hero-left {
    padding: 0.55rem 0 0.4rem 0;
}
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.66rem;
    font-weight: 500;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #818cf8;
    background: rgba(99,102,241,0.09);
    border: 1px solid rgba(99,102,241,0.22);
    border-radius: 99px;
    padding: 3px 10px;
    margin-bottom: 0.45rem;
}
.hero-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.9rem;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -1.2px;
    background: linear-gradient(135deg, #6366f1 0%, #a78bfa 45%, #22d3ee 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.35rem;
}
.hero-sub {
    font-size: 0.82rem;
    font-weight: 400;
    color: #64748b;
    line-height: 1.5;
    margin-bottom: 0;
}
.hero-sub strong {
    color: #475569;
    font-weight: 600;
}
.hero-pills { display: none; }

/* ── Hero right panel ── */
.hero-panel {
    background: rgba(255,255,255,0.55);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1.5px solid rgba(199,210,254,0.6);
    border-radius: 14px;
    padding: 0.75rem 1rem;
    margin-top: 0.55rem;
    box-shadow:
        0 4px 24px rgba(99,102,241,0.07),
        inset 0 1px 0 rgba(255,255,255,0.6);
}
.hero-panel-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    font-weight: 700;
    color: #818cf8;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 0.45rem;
}
.panel-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.28rem 0;
    border-bottom: 1px solid rgba(226,232,240,0.5);
}
.panel-item:last-child { border-bottom: none; }
.panel-icon { font-size: 0.88rem; flex-shrink: 0; }
.panel-text {
    font-size: 0.78rem;
    color: #334155;
    font-weight: 500;
    line-height: 1.3;
}

/* ── Footer ── */
.footer {
    text-align: center;
    padding: 2.5rem 0 1.5rem 0;
    margin-top: 1rem;
    border-top: 1px solid #f1f5f9;
}
.footer-main {
    font-size: 0.8rem;
    color: #94a3b8;
    font-weight: 500;
    opacity: 0.85;
    margin-bottom: 0.25rem;
}
.footer-main a { color: #818cf8; text-decoration: none; }
.footer-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #cbd5e1;
    opacity: 0.7;
    letter-spacing: 0.5px;
}

/* ── Upload zone ── */
.upload-wrap {
    background: linear-gradient(135deg, rgba(99,102,241,0.03) 0%, rgba(34,211,238,0.03) 100%);
    border: 2px dashed #c7d2fe;
    border-radius: 18px;
    padding: 2rem 1.5rem 1.4rem 1.5rem;
    margin-bottom: 1.2rem;
    transition: border-color 0.2s;
}
.upload-wrap:hover { border-color: #818cf8; }
.upload-heading {
    font-family: 'Inter', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #334155;
    text-align: center;
    margin-bottom: 0.25rem;
}
.upload-sub {
    font-size: 0.78rem;
    color: #94a3b8;
    text-align: center;
    margin-bottom: 0.9rem;
}
.fmt-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    justify-content: center;
    margin-bottom: 1rem;
}
.fmt-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.64rem;
    font-weight: 500;
    background: rgba(99,102,241,0.07);
    border: 1px solid rgba(99,102,241,0.18);
    color: #6366f1;
    border-radius: 5px;
    padding: 2px 8px;
}

/* ── Section label ── */
.sec-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    font-weight: 700;
    color: #94a3b8;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    display: block;
    margin-bottom: 0.55rem;
}

/* ── Stat chips ── */
.stat-chip {
    display: inline-block;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 3px 9px;
    font-size: 0.75rem;
    color: #475569;
    margin-right: 4px;
    margin-bottom: 4px;
    font-family: 'JetBrains Mono', monospace;
}

/* ── OCR badge ── */
.ocr-yes {
    display: inline-block;
    background: rgba(254,243,199,0.7);
    border: 1px solid #fbbf24;
    border-radius: 6px;
    padding: 3px 9px;
    font-size: 0.7rem;
    color: #92400e;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
}
.ocr-no {
    display: inline-block;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 3px 9px;
    font-size: 0.7rem;
    color: #94a3b8;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Token backend badge ── */
.token-backend {
    display: inline-block;
    background: rgba(34,211,238,0.08);
    border: 1px solid rgba(34,211,238,0.3);
    border-radius: 6px;
    padding: 3px 9px;
    font-size: 0.68rem;
    color: #0e7490;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
}

/* ── Result card ── */
.r-card {
    border: 1.5px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.25rem 1.4rem 0.7rem 1.4rem;
    margin-bottom: 1.3rem;
    background: #ffffff;
    box-shadow: 0 1px 4px rgba(15,23,42,0.04);
    transition: box-shadow 0.2s, border-color 0.2s;
}
.r-card:hover {
    box-shadow: 0 4px 20px rgba(15,23,42,0.08);
    border-color: #c7d2fe;
}
.r-card-ok  { border-left: 4px solid #22c55e; }
.r-card-err { border-left: 4px solid #ef4444; }
.r-filename {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.3rem;
    word-break: break-all;
}

/* ── Optimization stats ── */
.opt-row {
    display: flex;
    gap: 0.7rem;
    flex-wrap: wrap;
    margin: 0.8rem 0 0.9rem 0;
}
.opt-cell {
    flex: 1;
    min-width: 88px;
    background: #f8fafc;
    border: 1.5px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.65rem 0.8rem;
    text-align: center;
}
.opt-cell .lbl {
    font-size: 0.62rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.2rem;
    font-family: 'JetBrains Mono', monospace;
}
.opt-cell .val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.95rem;
    font-weight: 700;
    color: #1e293b;
}
.opt-cell.green { background: rgba(220,252,231,0.5); border-color: #86efac; }
.opt-cell.green .val { color: #15803d; }

/* ── Sidebar ── */
.sb-brand {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    font-weight: 700;
    background: linear-gradient(135deg, #6366f1, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.15rem;
}
.sb-tagline {
    font-size: 0.72rem;
    color: #64748b;
    line-height: 1.45;
    margin-bottom: 0.75rem;
}
.sb-status {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #16a34a;
    display: flex;
    align-items: center;
    gap: 4px;
    margin-bottom: 2px;
}

/* ── Compact How It Works (sidebar) ── */
.hiw-row {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.45rem 0;
    border-bottom: 1px solid #f1f5f9;
}
.hiw-row:last-child { border-bottom: none; }
.hiw-icon { font-size: 0.95rem; flex-shrink: 0; margin-top: 1px; }
.hiw-step {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    font-weight: 700;
    color: #334155;
    margin-bottom: 0;
    line-height: 1.3;
}
.hiw-desc-sm { font-size: 0.68rem; color: #94a3b8; line-height: 1.35; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 3.5rem 2rem;
    border: 2px dashed #e2e8f0;
    border-radius: 18px;
    margin-top: 0.5rem;
    background: rgba(248,250,252,0.5);
}
.empty-icon { font-size: 3rem; margin-bottom: 0.75rem; }
.empty-title {
    font-family: 'Inter', sans-serif;
    font-size: 0.95rem;
    font-weight: 600;
    color: #475569;
    margin-bottom: 0.35rem;
}
.empty-sub { font-size: 0.8rem; color: #94a3b8; }

/* ── Dark mode overrides ── */
@media (prefers-color-scheme: dark) {
    .hero-sub { color: #94a3b8; }
    .hero-sub strong { color: #cbd5e1; }
    .hero-panel {
        background: rgba(15,23,42,0.65);
        border-color: rgba(99,102,241,0.25);
        box-shadow: 0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
    }
    .panel-text { color: #cbd5e1; }
    .panel-item { border-bottom-color: rgba(51,65,85,0.6); }
    .upload-wrap { background: rgba(99,102,241,0.04); border-color: #3730a3; }
    .upload-heading { color: #e2e8f0; }
    .r-card { background: #0f172a; border-color: #1e293b; }
    .r-filename { color: #f1f5f9; }
    .stat-chip { background: #1e293b; border-color: #334155; color: #94a3b8; }
    .opt-cell { background: #1e293b; border-color: #334155; }
    .opt-cell .val { color: #f1f5f9; }
    .opt-cell.green { background: rgba(20,83,45,0.3); border-color: #166534; }
    .opt-cell.green .val { color: #4ade80; }
    .hiw-row { border-bottom-color: #1e293b; }
    .hiw-step { color: #cbd5e1; }
    .empty-state { background: rgba(15,23,42,0.5); border-color: #1e293b; }
    .empty-title { color: #94a3b8; }
    .footer { border-top-color: #1e293b; }
    .footer-main { color: #64748b; }
    .footer-sub { color: #475569; }
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown('<div class="sb-brand">◈ MarkItDown</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sb-tagline">Convert documents into AI-ready Markdown</div>',
        unsafe_allow_html=True,
    )

    # Show which token backend is active
    backend_label = "tiktoken (exact)" if TOKEN_BACKEND == "tiktoken" else "heuristic (chars/4)"
    st.markdown(
        f'<div class="sb-status">✓ OCR Ready</div>'
        f'<div class="sb-status">✓ Optimization Ready</div>'
        f'<div class="sb-status">✓ Tokens: {backend_label}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Smart Chunking ──
    st.markdown('<span class="sec-label">Smart Chunking</span>', unsafe_allow_html=True)
    chunk_option = st.selectbox(
        "Chunk Size",
        options=["None", "4K tokens", "8K tokens", "16K tokens", "Custom"],
        index=0,
        label_visibility="collapsed",
    )
    custom_chunk_size = None
    if chunk_option == "Custom":
        custom_chunk_size = st.number_input(
            "Custom token limit", min_value=500, max_value=128000, value=4000, step=500
        )

    # ── Chunk Overlap ──
    if chunk_option != "None":
        st.markdown(
            '<span class="sec-label" style="margin-top:0.6rem">Chunk Overlap</span>',
            unsafe_allow_html=True,
        )
        overlap_pct = st.slider(
            "Overlap %",
            min_value=0,
            max_value=25,
            value=10,
            step=5,
            label_visibility="collapsed",
            help="Percentage of each chunk's tokens to repeat at the start of the next chunk. "
                 "Helps LLMs retain context across boundaries. 0 = no overlap.",
        )
        st.caption(f"~{overlap_pct}% of chunk size repeated between chunks")
    else:
        overlap_pct = 0

    st.markdown("---")

    # ── Compact How It Works ──
    st.markdown('<span class="sec-label">How It Works</span>', unsafe_allow_html=True)
    st.markdown("""
    <div>
      <div class="hiw-row">
        <div class="hiw-icon">📁</div>
        <div class="hiw-text">
          <div class="hiw-step">Upload</div>
          <div class="hiw-desc-sm">Drop any file type</div>
        </div>
      </div>
      <div class="hiw-row">
        <div class="hiw-icon">⚙️</div>
        <div class="hiw-text">
          <div class="hiw-step">Convert</div>
          <div class="hiw-desc-sm">Extract structured Markdown</div>
        </div>
      </div>
      <div class="hiw-row">
        <div class="hiw-icon">🔍</div>
        <div class="hiw-text">
          <div class="hiw-step">OCR</div>
          <div class="hiw-desc-sm">Automatic text extraction</div>
        </div>
      </div>
      <div class="hiw-row">
        <div class="hiw-icon">✨</div>
        <div class="hiw-text">
          <div class="hiw-step">Optimize</div>
          <div class="hiw-desc-sm">Reduce token usage</div>
        </div>
      </div>
      <div class="hiw-row">
        <div class="hiw-icon">🤖</div>
        <div class="hiw-text">
          <div class="hiw-step">Ready</div>
          <div class="hiw-desc-sm">Use with ChatGPT, Claude, Gemini</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Recent Conversions ──
    if st.session_state.history:
        st.markdown('<span class="sec-label">Recent Conversions</span>', unsafe_allow_html=True)
        for item in reversed(st.session_state.history[-10:]):
            icon = "✅" if item["success"] else "❌"
            st.caption(f"{icon} {item['name']}")
        if st.button("Clear History", use_container_width=True):
            st.session_state.history = []
            st.rerun()

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

hero_left, hero_right = st.columns([1.05, 0.95], gap="large")

with hero_left:
    st.markdown("""
    <div class="hero-left">
      <div class="hero-eyebrow">⚡ Powered by Microsoft MarkItDown</div>
      <div class="hero-title">Document → Markdown</div>
      <div class="hero-sub">
        Convert any file into AI-ready Markdown with automatic OCR and token optimization.
      </div>
    </div>
    """, unsafe_allow_html=True)

with hero_right:
    st.markdown("""
    <div class="hero-panel">
      <div class="hero-panel-title">Why MarkItDown?</div>
      <div class="panel-item"><span class="panel-icon">📄</span><span class="panel-text">✓ 15+ File Formats</span></div>
      <div class="panel-item"><span class="panel-icon">🔍</span><span class="panel-text">✓ Automatic OCR</span></div>
      <div class="panel-item"><span class="panel-icon">✨</span><span class="panel-text">✓ Token Optimization</span></div>
      <div class="panel-item"><span class="panel-icon">🔀</span><span class="panel-text">✓ Smart Chunking</span></div>
      <div class="panel-item"><span class="panel-icon">🤖</span><span class="panel-text">✓ AI Ready</span></div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Upload zone
# ---------------------------------------------------------------------------

st.markdown("""
<div class="upload-wrap">
  <div class="upload-heading">Drag &amp; Drop Files Here</div>
  <div class="upload-sub">PDF · DOCX · PPTX · XLSX · CSV · HTML · TXT · JSON · JPG · PNG · WEBP · EPUB · ZIP and more</div>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Upload files",
    accept_multiple_files=True,
    label_visibility="collapsed",
)

col_btn, col_clr, _ = st.columns([1.2, 1, 5])
with col_btn:
    convert_btn = st.button("▶  Convert All", type="primary", use_container_width=True)
with col_clr:
    if st.button("✕  Clear", use_container_width=True):
        st.session_state.results = []
        st.rerun()

# ---------------------------------------------------------------------------
# Chunk size + overlap resolver
# ---------------------------------------------------------------------------

def _resolve_chunk_size() -> int | None:
    if chunk_option == "None":
        return None
    if chunk_option == "Custom":
        return custom_chunk_size
    return CHUNK_PRESETS.get(chunk_option)


def _resolve_overlap(chunk_size: int) -> int:
    """Convert the sidebar overlap percentage to an absolute token count."""
    return max(0, int(chunk_size * overlap_pct / 100))

# ---------------------------------------------------------------------------
# Conversion (OCR + Optimization always-on)
# ---------------------------------------------------------------------------

if convert_btn and uploaded_files:
    results = []
    progress = st.progress(0, text="Starting…")
    total = len(uploaded_files)

    for idx, uf in enumerate(uploaded_files):
        progress.progress(idx / total, text=f"Converting {uf.name}…")

        if not converter.is_supported(uf.name):
            st.warning(f"Unsupported file type: **{uf.name}** — skipped.")
            continue

        uuid_path, original_name = converter.save_upload(uf.name, uf.getvalue())
        result = converter.convert(uuid_path, original_name=original_name)

        # Always-on OCR fallback
        if result.success and needs_ocr_fallback(result.markdown, uuid_path):
            ocr_text, ocr_warning = run_ocr(uuid_path)
            if ocr_text:
                result.markdown = ocr_text
                result.ocr_used = True
                result._compute_stats()
            if ocr_warning:
                result.ocr_warning = ocr_warning

        # Always-on optimization
        if result.success and result.markdown:
            opt_md = optimize_markdown(result.markdown)
            opt_stats = OptimizationStats(
                original_text=result.markdown,
                optimized_text=opt_md,
            )
            st.session_state[f"opt_result_{original_name}"] = (opt_md, opt_stats)

        results.append(result)
        st.session_state.history.append(
            {"name": original_name, "success": result.success}
        )
        progress.progress((idx + 1) / total, text=f"Done {idx + 1}/{total}")

    progress.empty()
    st.session_state.results = results

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

results: list = st.session_state.results

if results:
    st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<span class="sec-label">Results</span>', unsafe_allow_html=True)

    successful = [r for r in results if r.success and r.output_path]
    if len(successful) > 1:
        zip_bytes, skipped = build_zip([r.output_path for r in successful])
        st.download_button(
            "⬇  Download All as ZIP",
            data=zip_bytes,
            file_name="converted_markdown.zip",
            mime="application/zip",
        )
        if skipped:
            st.warning(f"⚠️ {len(skipped)} file(s) were missing from disk and excluded from the ZIP: {', '.join(skipped)}")
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    for result in results:
        card_cls = "r-card r-card-ok" if result.success else "r-card r-card-err"
        st.markdown(f'<div class="{card_cls}">', unsafe_allow_html=True)

        col_name, col_meta = st.columns([3, 2])
        with col_name:
            st.markdown(
                f'<div class="r-filename">📄 {result.source_name}</div>',
                unsafe_allow_html=True,
            )
        with col_meta:
            ocr_badge = (
                '<span class="ocr-yes">⚡ OCR Applied</span>'
                if result.ocr_used
                else '<span class="ocr-no">No OCR needed</span>'
            )
            size_kb = result.file_size_bytes / 1024
            st.markdown(
                f'<span class="stat-chip">{size_kb:.1f} KB</span>'
                f'<span class="stat-chip">{result.duration_s:.2f}s</span>'
                f' {ocr_badge}',
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        if not result.success:
            st.error(f"Conversion failed: {result.error}")
            continue

        # Stats row — token count now comes from the consistent token_counter backend
        st.markdown(
            f'<span class="stat-chip">~{format_stat(result.token_estimate)} tokens</span>'
            f'<span class="stat-chip">{format_stat(result.word_count)} words</span>'
            f'<span class="stat-chip">{format_stat(result.char_count)} chars</span>',
            unsafe_allow_html=True,
        )

        if result.ocr_warning:
            st.caption(f"⚠️ {result.ocr_warning}")

        tabs = st.tabs(["📝 Preview", "✨ Optimized", "🔀 Chunks", "⬛ Raw"])

        # ── Preview ──
        with tabs[0]:
            preview_text = result.markdown[:3000]
            if len(result.markdown) > 3000:
                preview_text += "\n\n… *(truncated — see Raw tab for full content)*"
            st.code(preview_text, language="markdown")

            col_dl, col_cp = st.columns(2)
            with col_dl:
                st.download_button(
                    "⬇  Download Markdown",
                    data=result.markdown.encode("utf-8"),
                    file_name=Path(result.source_name).stem + ".md",
                    mime="text/markdown",
                    key=f"dl_{result.source_name}",
                    use_container_width=True,
                )
            with col_cp:
                st.text_area(
                    "copy",
                    value=result.markdown,
                    height=68,
                    key=f"cp_{result.source_name}",
                    label_visibility="collapsed",
                    help="Select all and copy",
                )

        # ── Optimized ──
        with tabs[1]:
            opt_data = st.session_state.get(f"opt_result_{result.source_name}")

            if not opt_data:
                if st.button("✨ Run Optimization", key=f"opt_now_{result.source_name}"):
                    opt_md = optimize_markdown(result.markdown)
                    opt_stats = OptimizationStats(
                        original_text=result.markdown,
                        optimized_text=opt_md,
                    )
                    opt_data = (opt_md, opt_stats)
                    st.session_state[f"opt_result_{result.source_name}"] = opt_data
                    st.rerun()

            if opt_data:
                opt_md, opt_stats = opt_data
                st.markdown(
                    f"""
                    <div class="opt-row">
                      <div class="opt-cell">
                        <div class="lbl">Original</div>
                        <div class="val">{opt_stats.fmt_original()}</div>
                      </div>
                      <div class="opt-cell">
                        <div class="lbl">Optimized</div>
                        <div class="val">{opt_stats.fmt_optimized()}</div>
                      </div>
                      <div class="opt-cell green">
                        <div class="lbl">Saved</div>
                        <div class="val">{opt_stats.fmt_saved()}</div>
                      </div>
                      <div class="opt-cell green">
                        <div class="lbl">% Saved</div>
                        <div class="val">{opt_stats.fmt_percent()}</div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.code(opt_md[:3000], language="markdown")
                col_odl, col_ocp = st.columns(2)
                with col_odl:
                    st.download_button(
                        "⬇  Download Optimized",
                        data=opt_md.encode("utf-8"),
                        file_name=Path(result.source_name).stem + "_optimized.md",
                        mime="text/markdown",
                        key=f"odl_{result.source_name}",
                        use_container_width=True,
                    )
                with col_ocp:
                    st.text_area(
                        "copy opt",
                        value=opt_md,
                        height=68,
                        key=f"ocp_{result.source_name}",
                        label_visibility="collapsed",
                        help="Select all and copy",
                    )
            else:
                st.info("Optimization will appear here automatically after conversion.")

        # ── Chunks ──
        with tabs[2]:
            chunk_size = _resolve_chunk_size()
            if chunk_size is None:
                st.info("Select a chunk size in the sidebar to split this document.")
            else:
                overlap_tok = _resolve_overlap(chunk_size)
                if st.button("🔀 Generate Chunks", key=f"chunk_{result.source_name}"):
                    source_text = result.markdown
                    opt_local = st.session_state.get(f"opt_result_{result.source_name}")
                    if opt_local:
                        source_text = opt_local[0]
                    chunks = chunk_markdown(source_text, chunk_size, overlap_tokens=overlap_tok)
                    st.session_state[f"chunks_{result.source_name}"] = chunks

                chunks = st.session_state.get(f"chunks_{result.source_name}")
                if chunks:
                    overlap_note = f", ~{overlap_pct}% overlap" if overlap_tok > 0 else ""
                    st.caption(
                        f"Generated **{len(chunks)}** chunks "
                        f"(≤ {format_stat(chunk_size)} tokens each{overlap_note})"
                    )
                    stem = Path(result.source_name).stem
                    chunk_items = [
                        (f"{stem}_chunk_{i+1:03d}.md", ch)
                        for i, ch in enumerate(chunks)
                    ]
                    zip_chunks = build_zip_from_strings(chunk_items)
                    st.download_button(
                        "⬇  Download All Chunks as ZIP",
                        data=zip_chunks,
                        file_name=f"{stem}_chunks.zip",
                        mime="application/zip",
                        key=f"chunkdl_{result.source_name}",
                    )
                    st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)
                    for i, chunk in enumerate(chunks):
                        with st.expander(
                            f"Chunk {i+1}  —  ~{format_stat(estimate_tokens(chunk))} tokens"
                        ):
                            st.code(chunk, language="markdown")

        # ── Raw ──
        with tabs[3]:
            st.text_area(
                "full raw",
                value=result.markdown,
                height=420,
                key=f"raw_{result.source_name}",
                label_visibility="collapsed",
            )

elif not uploaded_files:
    st.markdown("""
    <div class="empty-state">
      <div class="empty-icon">📂</div>
      <div class="empty-title">No files uploaded yet</div>
      <div class="empty-sub">
        Drop files into the upload area above, then click
        <strong>Convert All</strong> to get started.
      </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown("""
<div class="footer">
  <div class="footer-main">
    Made by <strong>Jaidev-cr7</strong> with ❤️
  </div>
  <div class="footer-sub">Powered by Microsoft MarkItDown</div>
</div>
""", unsafe_allow_html=True)