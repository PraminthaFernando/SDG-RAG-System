import fitz
from pathlib import Path
import time

from .models import PageContent, IngestedDocument


class PDFLoader:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def _inside_bbox(self, word, bbox):
        x0, y0, x1, y1 = word[:4]
        bx0, by0, bx1, by1 = bbox
        return x0 >= bx0 and x1 <= bx1 and y0 >= by1 and y1 <= by0

    def extract_text_from_page(self, page, table_boxes=None):

        t0 = time.time()
        words = page.get_text("words")
        print(f"      🔤 words extracted: {len(words)} in {round(time.time() - t0, 2)}s")

        filtered_words = []

        t0 = time.time()
        for word in words:

            if table_boxes:
                if any(self._inside_bbox(word, box) for box in table_boxes):
                    continue

            filtered_words.append(word[4])

        print(f"      🧹 words filtered: {len(filtered_words)} in {round(time.time() - t0, 2)}s")

        return " ".join(filtered_words)

    def load(self, pid: str, filename: str, table_boxes_per_page=None) -> IngestedDocument:

        start_total = time.time()

        file_path = self.base_path / filename

        print(f"\n📄 [{pid}] Opening PDF: {file_path}")

        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} not found.")

        t0 = time.time()
        pdf = fitz.open(file_path)
        print(f"✅ [{pid}] PDF opened in {round(time.time() - t0, 2)}s | pages={len(pdf)}")

        pages = []

        for i, page in enumerate(pdf, start=1):

            page_start = time.time()

            print(f"\n➡️ [{pid}] Page {i}/{len(pdf)}")

            boxes = None
            if table_boxes_per_page:
                boxes = table_boxes_per_page.get(i, [])
                print(f"   📦 table boxes: {len(boxes)}")

            # ---- extract text ----
            t0 = time.time()
            page_text = self.extract_text_from_page(page, boxes)
            print(f"   📝 text extracted in {round(time.time() - t0, 2)}s | length={len(page_text)}")

            pages.append(
                PageContent(
                    page=i,
                    text=page_text
                )
            )

            print(f"   ⏱️ page done in {round(time.time() - page_start, 2)}s")

        print(f"\n🎉 [{pid}] PDF LOAD COMPLETE in {round(time.time() - start_total, 2)}s")

        return IngestedDocument(
            pid=pid,
            name=filename,
            pages=pages
        )