import os
import io
import json
import subprocess
from pathlib import Path
from typing import List, Tuple
import structlog

logger = structlog.get_logger()


class DocumentProcessor:
    """Extracts raw text from uploaded documents."""

    # Map extension → canonical MIME type (used for validation and display)
    SUPPORTED_TYPES: dict[str, str] = {
        # ── PDF ──────────────────────────────────────────────────────────────
        "pdf":  "application/pdf",
        # ── Microsoft Office — modern OOXML ──────────────────────────────────
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        # ── Microsoft Office — legacy binary ─────────────────────────────────
        "doc":  "application/msword",
        "xls":  "application/vnd.ms-excel",
        # ── OpenDocument (LibreOffice / Apache OpenOffice) ───────────────────
        "odt":  "application/vnd.oasis.opendocument.text",
        "ods":  "application/vnd.oasis.opendocument.spreadsheet",
        "odp":  "application/vnd.oasis.opendocument.presentation",
        # ── Rich text & markup ────────────────────────────────────────────────
        "rtf":  "application/rtf",
        "html": "text/html",
        "htm":  "text/html",
        "xml":  "application/xml",
        "epub": "application/epub+zip",
        # ── Plain text variants ───────────────────────────────────────────────
        "txt":  "text/plain",
        "md":   "text/markdown",
        "rst":  "text/x-rst",
        "log":  "text/plain",
        "ini":  "text/plain",
        "cfg":  "text/plain",
        "conf": "text/plain",
        "toml": "application/toml",
        # ── Data / structured ─────────────────────────────────────────────────
        "csv":  "text/csv",
        "tsv":  "text/tab-separated-values",
        "json": "application/json",
        "yaml": "application/x-yaml",
        "yml":  "application/x-yaml",
    }

    @classmethod
    def get_file_type(cls, filename: str) -> str:
        return Path(filename).suffix.lower().lstrip(".")

    @classmethod
    def extract_text(cls, file_path: str, file_type: str) -> Tuple[str, int]:
        """Returns (text, page_count). Raises ValueError for unsupported types."""
        extractors = {
            # PDF
            "pdf":  cls._extract_pdf,
            # OOXML
            "docx": cls._extract_docx,
            "xlsx": cls._extract_xlsx,
            "pptx": cls._extract_pptx,
            # Legacy binary
            "doc":  cls._extract_doc,
            "xls":  cls._extract_xls,
            # OpenDocument
            "odt":  cls._extract_odt,
            "ods":  cls._extract_ods,
            "odp":  cls._extract_odp,
            # Rich text & markup
            "rtf":  cls._extract_rtf,
            "html": cls._extract_html,
            "htm":  cls._extract_html,
            "xml":  cls._extract_xml,
            "epub": cls._extract_epub,
            # Plain text (all variants share the same reader)
            "txt":  cls._extract_txt,
            "md":   cls._extract_txt,
            "rst":  cls._extract_txt,
            "log":  cls._extract_txt,
            "ini":  cls._extract_txt,
            "cfg":  cls._extract_txt,
            "conf": cls._extract_txt,
            # Data / structured
            "csv":  cls._extract_csv,
            "tsv":  cls._extract_tsv,
            "json": cls._extract_json,
            "yaml": cls._extract_yaml,
            "yml":  cls._extract_yaml,
            "toml": cls._extract_toml,
        }
        extractor = extractors.get(file_type)
        if not extractor:
            raise ValueError(f"Unsupported file type: .{file_type}")
        return extractor(file_path)

    # ── PDF ──────────────────────────────────────────────────────────────────

    @classmethod
    def _extract_pdf(cls, file_path: str) -> Tuple[str, int]:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        pages = [page.get_text() for page in doc if page.get_text().strip()]
        doc.close()
        return "\n\n".join(pages), len(pages)

    # ── Microsoft Office — OOXML ─────────────────────────────────────────────

    @classmethod
    def _extract_docx(cls, file_path: str) -> Tuple[str, int]:
        from docx import Document
        doc = Document(file_path)
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                line = "\t".join(cell.text.strip() for cell in row.cells)
                if line.strip():
                    parts.append(line)
        return "\n\n".join(parts), 1

    @classmethod
    def _extract_xlsx(cls, file_path: str) -> Tuple[str, int]:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        rows = []
        for name in wb.sheetnames:
            rows.append(f"[Sheet: {name}]")
            for row in wb[name].iter_rows(values_only=True):
                line = "\t".join("" if v is None else str(v) for v in row)
                if line.strip():
                    rows.append(line)
        wb.close()
        return "\n".join(rows), len(wb.sheetnames)

    @classmethod
    def _extract_pptx(cls, file_path: str) -> Tuple[str, int]:
        from pptx import Presentation
        prs = Presentation(file_path)
        slides = []
        for slide in prs.slides:
            parts = [
                shape.text.strip()
                for shape in slide.shapes
                if hasattr(shape, "text") and shape.text.strip()
            ]
            if parts:
                slides.append("\n".join(parts))
        return "\n\n---\n\n".join(slides), len(prs.slides)

    # ── Microsoft Office — legacy binary ────────────────────────────────────

    @classmethod
    def _extract_doc(cls, file_path: str) -> Tuple[str, int]:
        # antiword is a small system package installed in the Docker image
        try:
            result = subprocess.run(
                ["antiword", file_path],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                return result.stdout, 1
            raise ValueError(f"antiword returned exit code {result.returncode}: {result.stderr.strip()}")
        except FileNotFoundError:
            raise ValueError(
                "Extracting .doc files requires the 'antiword' system package. "
                "Convert the file to .docx, or rebuild the Docker image."
            )

    @classmethod
    def _extract_xls(cls, file_path: str) -> Tuple[str, int]:
        import xlrd
        wb = xlrd.open_workbook(file_path)
        rows = []
        for sheet in wb.sheets():
            rows.append(f"[Sheet: {sheet.name}]")
            for rx in range(sheet.nrows):
                line = "\t".join(str(sheet.cell_value(rx, cx)) for cx in range(sheet.ncols))
                if line.strip():
                    rows.append(line)
        return "\n".join(rows), wb.nsheets

    # ── OpenDocument formats (LibreOffice / Apache OpenOffice) ───────────────

    @classmethod
    def _extract_odt(cls, file_path: str) -> Tuple[str, int]:
        from odf.opendocument import load
        from odf.text import P
        from odf import teletype
        doc = load(file_path)
        paragraphs = [
            teletype.extractText(p)
            for p in doc.getElementsByType(P)
        ]
        text = "\n\n".join(p for p in paragraphs if p.strip())
        return text, 1

    @classmethod
    def _extract_ods(cls, file_path: str) -> Tuple[str, int]:
        from odf.opendocument import load
        from odf.table import Table, TableRow, TableCell
        from odf import teletype
        doc = load(file_path)
        rows = []
        for table in doc.getElementsByType(Table):
            for row in table.getElementsByType(TableRow):
                cells = [teletype.extractText(c) for c in row.getElementsByType(TableCell)]
                line = "\t".join(cells)
                if line.strip():
                    rows.append(line)
        return "\n".join(rows), 1

    @classmethod
    def _extract_odp(cls, file_path: str) -> Tuple[str, int]:
        from odf.opendocument import load
        from odf.draw import Page
        from odf.text import P
        from odf import teletype
        doc = load(file_path)
        pages = doc.getElementsByType(Page)
        slides = []
        for page in pages:
            parts = [
                teletype.extractText(p)
                for p in page.getElementsByType(P)
                if teletype.extractText(p).strip()
            ]
            if parts:
                slides.append("\n".join(parts))
        return "\n\n---\n\n".join(slides), len(pages)

    # ── Rich text & markup ───────────────────────────────────────────────────

    @classmethod
    def _extract_rtf(cls, file_path: str) -> Tuple[str, int]:
        from striprtf.striprtf import rtf_to_text
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            text = rtf_to_text(f.read())
        return text, 1

    @classmethod
    def _extract_html(cls, file_path: str) -> Tuple[str, int]:
        from bs4 import BeautifulSoup
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text, 1

    @classmethod
    def _extract_xml(cls, file_path: str) -> Tuple[str, int]:
        from bs4 import BeautifulSoup
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            soup = BeautifulSoup(f.read(), "xml")
        text = soup.get_text(separator="\n", strip=True)
        return text, 1

    @classmethod
    def _extract_epub(cls, file_path: str) -> Tuple[str, int]:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
        book = epub.read_epub(file_path, options={"ignore_ncx": True})
        chapters = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), "html.parser")
                text = soup.get_text(separator="\n", strip=True)
                if text:
                    chapters.append(text)
        return "\n\n---\n\n".join(chapters), len(chapters)

    # ── Plain text ───────────────────────────────────────────────────────────

    @classmethod
    def _extract_txt(cls, file_path: str) -> Tuple[str, int]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(), 1

    # ── Data / structured ────────────────────────────────────────────────────

    @classmethod
    def _extract_csv(cls, file_path: str) -> Tuple[str, int]:
        import pandas as pd
        df = pd.read_csv(file_path, sep=None, engine="python")
        return df.to_string(index=False), 1

    @classmethod
    def _extract_tsv(cls, file_path: str) -> Tuple[str, int]:
        import pandas as pd
        df = pd.read_csv(file_path, sep="\t")
        return df.to_string(index=False), 1

    @classmethod
    def _extract_json(cls, file_path: str) -> Tuple[str, int]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        return json.dumps(data, indent=2, ensure_ascii=False), 1

    @classmethod
    def _extract_yaml(cls, file_path: str) -> Tuple[str, int]:
        import yaml
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            data = yaml.safe_load(f)
        return yaml.dump(data, default_flow_style=False, allow_unicode=True), 1

    @classmethod
    def _extract_toml(cls, file_path: str) -> Tuple[str, int]:
        import tomllib
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
        # Represent as JSON for readable, consistent text output
        return json.dumps(data, indent=2, default=str), 1

    # ── Shared utilities ─────────────────────────────────────────────────────

    @classmethod
    def clean_text(cls, text: str) -> str:
        import re
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = text.replace("\x00", "")
        return text.strip()

    @classmethod
    def chunk_text(cls, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """Word-based chunking with overlap."""
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunks.append(" ".join(words[start:end]))
            start += chunk_size - overlap
        return [c for c in chunks if c.strip()]

    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        return len(text) // 4  # ~4 chars per token
