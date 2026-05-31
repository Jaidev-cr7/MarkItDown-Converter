# LLM Markdown Converter

A clean, responsive Streamlit application that converts any document to clean, LLM-ready Markdown using [Microsoft MarkItDown](https://github.com/microsoft/markitdown) — with built-in OCR, token optimization, and smart chunking. Deploy locally or on Streamlit Community Cloud.

## ✨ Features

- **Drag & Drop Upload:** Batch-upload multiple files at once with a simple drag-and-drop interface.
- **Wide Format Support:** Converts PDF, DOCX, PPTX, XLSX, HTML, TXT, CSV, JSON, XML, Images, Audio, and EPUB.
- **OCR Fallback:** Automatically extracts text from scanned PDFs and images using [EasyOCR](https://github.com/JaidedAI/EasyOCR) — no system binary required, works on Streamlit Community Cloud.
- **Smart Embedded Image OCR:** Extracts images embedded inside DOCX, PDF, PPTX, and HTML documents and runs OCR, appending results directly into the Markdown.
- **Noise Filtering & Caching:** Smart OCR mode automatically skips decorative graphics, maps, and UI noise to prevent token bloat, while a SHA-256 cache ensures identical images are OCR'd exactly once.
- **GPU Acceleration:** EasyOCR automatically utilizes CUDA-compatible GPUs for blazing-fast inference, while seamlessly falling back to CPU when needed.
- **Performance Optimized OCR:** Large embedded images are automatically downscaled before processing (without altering filtering rules), drastically cutting CPU execution time by up to 70% with negligible accuracy loss.
- **Markdown Optimization:** Strips OCR artifacts, page numbers, duplicate headings, and excess whitespace to reduce token usage. Shows before/after token savings.
- **Smart Chunking:** Split large documents into LLM-friendly chunks (4K / 8K / 16K / Custom tokens) with adjustable overlap to retain context across boundaries, and download all chunks as a ZIP.
- **Markdown Preview:** Inspect rendered Markdown and raw text per file inside tabbed result cards.
- **Detailed Statistics:** Per-file character count, word count, exact BPE token count (via `tiktoken`), embedded images OCR’d count, file size, conversion time, and OCR status.
- **Batch Downloads:** Download individual `.md` files or grab all successful conversions as a single ZIP archive.
- **Session History:** Sidebar tracks your recent conversions during the session.
- **How It Works:** Step-by-step visual guide on the landing page (Upload → Convert → OCR → Optimize → Use with LLMs).
- **Cloud Ready:** No external executables or system dependencies — deployable directly to Streamlit Community Cloud.

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/llm-markdown-converter.git
cd llm-markdown-converter
```

### 2. Setup Virtual Environment
```powershell
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```
*(For Command Prompt, use `.\venv\Scripts\activate.bat`)*

**macOS / Linux:**
```bash
source venv/bin/activate
```

### 4. Install Requirements
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
streamlit run app.py
```

The application will open automatically in your default web browser at `http://localhost:8501`.

## ☁️ Streamlit Community Cloud Deployment

This app is fully compatible with [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Push the repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo.
3. Set **Main file path** to `app.py`.
4. Click **Deploy** — no additional secrets or system packages required.

> **Note:** EasyOCR downloads its model weights (~100 MB) on first use. Streamlit Community Cloud caches these automatically between reruns.

## 📁 Project Structure

```text
project/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Project dependencies
├── README.md                 # This file
├── tmp/
│   ├── uploads/              # Temporary storage for uploaded files (UUID-named)
│   └── converted/            # Temporary storage for generated .md files
└── utils/                    # Core modules
    ├── __init__.py
    ├── converter.py          # MarkItDown wrapper, embedded-image OCR merge, UUID path management
    ├── image_extractor.py    # Extracts embedded images from PDF/DOCX/PPTX/HTML for OCR
    ├── ocr_handler.py        # EasyOCR fallback + embedded-image OCR with SHA-256 cache
    ├── optimizer.py          # Markdown cleanup, token optimization, smart chunking
    ├── token_counter.py      # Word, character, and token estimation
    └── zip_handler.py        # In-memory ZIP archive generation
```

## ⚙️ Configuration

All settings are available in the sidebar at runtime — no config files needed. Each selector has an inline **ⓘ tooltip** explaining every option:

| Setting | Options | Description |
|---|---|---|
| **Embedded Image OCR** | `Disabled` | Skip OCR on all embedded images — fastest. |
| | `Smart (Recommended)` | OCR only images likely to contain useful text; filters logos, maps, and icons automatically. |
| | `Aggressive` | OCR every embedded image without any filtering. |
| **Smart Chunking** | `None` | No splitting — single Markdown output. Best for large-context LLMs (Claude, GPT-4). |
| | `4K tokens` | For GPT-3.5 and small-context models. |
| | `8K tokens` | For GPT-4 8K and older Claude models. |
| | `16K tokens` | For most modern models. |
| | `Custom` | Set your own token limit (500 – 128 000). |
| **Chunk Overlap** | `0 – 25 %` | Percentage of tokens repeated at the start of the next chunk to preserve context across boundaries. |

> **Note:** Whole-document OCR fallback and Markdown optimization are **always-on automatic**. Standalone image uploads bypass smart filters and are always OCR'd.

## 🛠️ Built With

- [Streamlit](https://streamlit.io/) — UI framework
- [Microsoft MarkItDown](https://github.com/microsoft/markitdown) — document-to-Markdown conversion
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) — OCR for images and scanned PDFs
- [PyMuPDF](https://pymupdf.readthedocs.io/) — PDF embedded image extraction
- [python-docx](https://python-docx.readthedocs.io/) — DOCX embedded image extraction
- [python-pptx](https://python-pptx.readthedocs.io/) — PPTX embedded image extraction
- [pdf2image](https://github.com/Belval/pdf2image) — PDF page rendering for fallback OCR
- [Pillow](https://python-pillow.org/) — image processing and normalisation
- [tiktoken](https://github.com/openai/tiktoken) — exact BPE token counts for OpenAI models