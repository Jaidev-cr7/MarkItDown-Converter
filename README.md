# LLM Markdown Converter

A clean, responsive Streamlit application that converts various document formats to Markdown using the [Microsoft MarkItDown](https://github.com/microsoft/markitdown) library. This local-first tool is perfect for preparing documents for use with LLMs like ChatGPT, Claude, Gemini, and NotebookLM.

## ✨ Features

- **Drag & Drop Upload:** Easy-to-use file uploader supporting both single and multi-file uploads.
- **Wide Format Support:** Converts PDF, DOCX, PPTX, XLSX, HTML, TXT, CSV, JSON, XML, Images (OCR), and EPUB.
- **Markdown Preview:** Built-in viewer to check rendered Markdown and raw text side-by-side.
- **Detailed Statistics:** Displays character count, word count, estimated token count, and file size for each conversion.
- **Batch Downloads:** Download individual files or grab all successful conversions as a single ZIP archive.
- **Session History:** Keeps track of your recent conversions during your session.
- **Local First:** No databases, no external storage. Everything happens locally on your machine.

## 🚀 Quick Start

### 1. Setup Virtual Environment
```powershell
python -m venv venv
```

### 2. Activate Virtual Environment
**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```
*(For Command Prompt, use `.\venv\Scripts\activate.bat`)*

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Requirements
```powershell
pip install -r requirements.txt
```

### 4. Run the Application
```powershell
streamlit run app.py
```
The application will open automatically in your default web browser at `http://localhost:8501`.

## 📁 Project Structure

```text
project/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Project dependencies
├── uploads/                # Temporary storage for uploaded files
├── converted/              # Temporary storage for generated .md files
└── utils/                  # Core modules
    ├── __init__.py
    ├── converter.py        # MarkItDown wrapper and file management
    ├── token_counter.py    # Word, character, and token estimation
    └── zip_handler.py      # In-memory ZIP archive generation
```

## 🛠️ Built With
- [Streamlit](https://streamlit.io/)
- [Microsoft MarkItDown](https://github.com/microsoft/markitdown)
