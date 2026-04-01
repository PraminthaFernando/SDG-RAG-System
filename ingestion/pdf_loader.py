import fitz
from pathlib import Path
from .models import PageContent, IngestedDocument

class PDFLoader:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def _inside_bbox(self, word, bbox):
        x0, y0, x1, y1 = word[:4]
        bx0, by0, bx1, by1 = bbox
        return x0 >= bx0 and x1 <= bx1 and y0 >= by1 and y1 <= by0

    def extract_text_from_page(self, page, table_boxes=None):

        words = page.get_text("words")
        filtered_words = []

        for word in words:

            if table_boxes:
                if any(self._inside_bbox(word, box) for box in table_boxes):
                    continue

            filtered_words.append(word[4])

        return " ".join(filtered_words)

    def load(self, pid: str, filename: str, table_boxes_per_page=None) -> IngestedDocument:

        file_path = self.base_path / filename

        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} not found.")

        pdf = fitz.open(file_path)

        pages = []

        for i, page in enumerate(pdf, start=1):

            boxes = None
            if table_boxes_per_page:
                boxes = table_boxes_per_page.get(i, [])

            page_text = self.extract_text_from_page(page, boxes)

            pages.append(
                PageContent(
                    page=i,
                    text=page_text
                )
            )

        return IngestedDocument(
            pid=pid,
            name=filename,
            pages=pages
        )