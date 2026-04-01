from pathlib import Path
from typing import List
import time

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

        start_total = time.time()
        print(f"\n🚀 [{pid}] START ingest: {filename}")

        pdf_path = str(Path(self.loader.base_path) / filename)

        # =========================
        # TABLE BOX DETECTION
        # =========================
        t0 = time.time()
        print(f"📦 [{pid}] Detecting table boxes...")
        table_boxes = self.table_extractor.get_table_boxes(pdf_path)
        print(f"✅ [{pid}] Table boxes detected in {round(time.time() - t0, 2)}s")

        # =========================
        # PDF LOAD
        # =========================
        t0 = time.time()
        print(f"📄 [{pid}] Loading PDF...")
        document = self.loader.load(pid, filename, table_boxes)
        print(f"✅ [{pid}] PDF loaded in {round(time.time() - t0, 2)}s | pages={len(document.pages)}")

        new_pages = []

        # =========================
        # PAGE LOOP
        # =========================
        for i, page in enumerate(document.pages, 1):

            page_start = time.time()
            print(f"\n➡️ [{pid}] Page {i}/{len(document.pages)}")

            # ---- Sentence split ----
            t0 = time.time()
            sentences = self.cleaner.split_sentences(page.text)
            print(f"   ✂️ split_sentences: {round(time.time() - t0, 2)}s")

            # ---- Clean ----
            t0 = time.time()
            sentences = self.cleaner.clean(sentences)
            print(f"   🧹 clean: {round(time.time() - t0, 2)}s")

            # ---- Table extraction (BIG SUSPECT) ----
            t0 = time.time()
            print(f"   📊 extracting tables...")
            table_texts = self.table_extractor.extract(pdf_path, page.page)
            print(f"   ✅ tables extracted: {len(table_texts)} in {round(time.time() - t0, 2)}s")

            # ---- Chunk ----
            t0 = time.time()
            chunks = self.chunker.chunk(sentences)
            print(f"   🧩 chunk: {len(chunks)} chunks in {round(time.time() - t0, 2)}s")

            chunks.extend(table_texts)

            for chunk in chunks:
                new_pages.append(
                    type(page)(
                        page=page.page,
                        text=chunk
                    )
                )

            print(f"   ⏱️ Page done in {round(time.time() - page_start, 2)}s")

        document.pages = new_pages

        print(f"\n🎉 [{pid}] DONE ingest {filename} in {round(time.time() - start_total, 2)}s")
        return document