from pathlib import Path
from typing import List
from .pdf_loader import PDFLoader
from .table_extractor import TableExtractor
from .cleaner import TextCleaner
from .chunker import TextChunker
from .models import IngestedDocument


class IngestionPipeline:

    def __init__(self, pdf_base_path: str):
        self.loader = PDFLoader(pdf_base_path)
        self.table_extractor = TableExtractor()
        self.cleaner = TextCleaner()
        self.chunker = TextChunker()

    def ingest(self, pid: str, filename: str) -> IngestedDocument:
        # document = self.loader.load(pid, filename)
        pdf_path = str(Path(self.loader.base_path) / filename)
        
        table_boxes = self.table_extractor.get_table_boxes(pdf_path)
        document = self.loader.load(pid, filename, table_boxes)

        new_pages = []

        for page in document.pages:
            sentences = self.cleaner.split_sentences(page.text)
            sentences = self.cleaner.clean(sentences)
            table_texts = self.table_extractor.extract(pdf_path, page.page)
            chunks = self.chunker.chunk(sentences)
            chunks.extend(table_texts)
            
            for chunk in chunks:
                new_pages.append(
                    type(page)(
                        page=page.page,
                        text=chunk
                    )
                )

        document.pages = new_pages

        return document