"""PDF utility functions for rendering and text extraction."""

import base64
from pathlib import Path
from typing import List, Dict, Any

import fitz


def page_to_png_bytes(doc: fitz.Document, page_index: int, dpi: int = 200) -> bytes:
    """Render PDF page to PNG bytes at specified DPI."""
    page = doc[page_index]
    scale = max(dpi / 72.0, 1.0)
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return pix.tobytes("png")


def extract_page_text(doc: fitz.Document, page_index: int, max_chars: int = 15000) -> str:
    """Extract plain text from PDF page."""
    page = doc[page_index]
    text = page.get_text("text", sort=True) or ""
    return text[:max_chars]



def discover_pdfs(input_dir: Path) -> List[Path]:
    """Discover all PDF files in input directory."""
    pdf_files = []
    for pdf_path in input_dir.rglob("*.pdf"):
        if pdf_path.is_file():
            pdf_files.append(pdf_path)
    return sorted(pdf_files)


def b64_png_bytes(png_bytes: bytes) -> str:
    """Convert PNG bytes to base64 data URL."""
    return f"data:image/png;base64,{base64.b64encode(png_bytes).decode('utf-8')}"