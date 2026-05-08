import os
import io
from pathlib import Path
from typing import List, Tuple
import structlog

logger = structlog.get_logger()


class DocumentProcessor:
    """Extracts raw text from uploaded documents."""

    SUPPORTED_TYPES = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
        "csv": "text/csv",
        "md": "text/markdown",
    }

    @classmethod
    def get_file_type(cls, filename: str) -> str:
        return Path(filename).suffix.lower().lstrip(".")

    @classmethod
    def extract_text(cls, file_path: str, file_type: str) -> Tuple[str, int]:
        """Returns (text, page_count)."""
        extractors = {
            "pdf": cls._extract_pdf,
            "docx": cls._extract_docx,
            "txt": cls._extract_txt,
            "md": cls._extract_txt,
            "csv": cls._extract_csv,
        }
        extractor = extractors.get(file_type)
        if not extractor:
            raise ValueError(f"Unsupported file type: {file_type}")
        return extractor(file_path)

    @classmethod
    def _extract_pdf(cls, file_path: str) -> Tuple[str, int]:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        pages = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                pages.append(text)
        doc.close()
        return "\n\n".join(pages), len(pages)

    @classmethod
    def _extract_docx(cls, file_path: str) -> Tuple[str, int]:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n\n".join(paragraphs)
        return text, 1

    @classmethod
    def _extract_txt(cls, file_path: str) -> Tuple[str, int]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        return text, 1

    @classmethod
    def _extract_csv(cls, file_path: str) -> Tuple[str, int]:
        import pandas as pd
        df = pd.read_csv(file_path)
        text = df.to_string(index=False)
        return text, 1

    @classmethod
    def clean_text(cls, text: str) -> str:
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\x00', '', text)
        return text.strip()

    @classmethod
    def chunk_text(cls, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """Simple character-based chunking with overlap."""
        words = text.split()
        chunks = []
        start = 0

        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start += chunk_size - overlap

        return [c for c in chunks if c.strip()]

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        return len(text) // 4  # ~4 chars per token
