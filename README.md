# LLM Markdown Converter

A clean, responsive Streamlit application that converts any document to clean, LLM-ready Markdown using [Microsoft MarkItDown](https://github.com/microsoft/markitdown) — with built-in OCR, token optimization, and smart chunking. Deploy locally or on Streamlit Community Cloud.

## ✨ Features

- **Drag & Drop Upload:** Batch-upload multiple files at once with a simple drag-and-drop interface.
- **Wide Format Support:** Converts PDF, DOCX, PPTX, XLSX, HTML, TXT, CSV, JSON, XML, Images, Audio, and EPUB.
- **OCR Fallback:** Automatically extracts text from scanned PDFs and images using [EasyOCR](https://github.com/JaidedAI/EasyOCR) — no system binary required, works on Streamlit Community Cloud.
- **Markdown Optimization:** Strips OCR artifacts, page numbers, duplicate headings, and excess whitespace to reduce token usage. Shows before/after token savings.
- **Smart Chunking:** Split large documents into LLM-friendly chunks (4K / 8K / 16K / Custom tokens) and download all chunks as a ZIP.
- **Markdown Preview:** Inspect rendered Markdown and raw text per file inside tabbed result cards.
- **Detailed Statistics:** Per-file character count, word count, estimated token count, file size, conversion time, and OCR status.
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
    ├── converter.py          # MarkItDown wrapper, UUID path management, file conversion
    ├── ocr_handler.py        # EasyOCR fallback for images and scanned PDFs
    ├── optimizer.py          # Markdown cleanup, token optimization, smart chunking
    ├── token_counter.py      # Word, character, and token estimation
    └── zip_handler.py        # In-memory ZIP archive generation
```

## ⚙️ Configuration

All settings are available in the sidebar at runtime — no config files needed:

| Setting | Description |
|---|---|
| **Enable OCR Fallback** | Run EasyOCR on images or scanned PDFs with little/no extracted text |
| **Auto-Optimize Markdown** | Automatically clean and deduplicate Markdown after conversion |
| **Chunk Size** | Split output into 4K / 8K / 16K / Custom token chunks for LLM context windows |

## 🛠️ Built With

- [Streamlit](https://streamlit.io/) — UI framework
- [Microsoft MarkItDown](https://github.com/microsoft/markitdown) — document-to-Markdown conversion
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) — OCR for images and scanned PDFs
- [pdf2image](https://github.com/Belval/pdf2image) — PDF page rendering for OCR
- [Pillow](https://python-pillow.org/) — image processing