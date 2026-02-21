from pdfminer.high_level import extract_text
import fitz
from pathlib import Path
from .models import PageContent, IngestedDocument


class PDFLoader:

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def extract_text_from_page(self, page):
        text = page.get_text()
        if not text:
            return ""
        return text

    def load(self, pid: str, filename: str) -> IngestedDocument:
        file_path = self.base_path / filename

        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} not found.")

        pdf = fitz.open(file_path)

        pages = []
                
        for i, page in enumerate(pdf, start=1):
            page_text = self.extract_text_from_page(page)
            pages.append(PageContent(page=i, text=page_text))

        return IngestedDocument(
            pid=pid,
            name=filename,
            pages=pages
        )