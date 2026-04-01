import camelot
import threading
from typing import List
import warnings
import time

warnings.filterwarnings("ignore", category=Warning)

_camelot_lock = threading.Lock()


class TableExtractor:

    def table_to_semantic_text(self, df) -> List[str]:
        headers = df.iloc[0]
        semantic_rows = []

        for i in range(1, len(df)):
            row = df.iloc[i]
            row_text_parts = []

            for col_index, cell in enumerate(row):
                header = headers[col_index].replace("\n", " ").strip()
                cell = str(cell).replace("\n", " ").strip()
                row_text_parts.append(f"{header}: {cell}")

            semantic_row = " | ".join(row_text_parts)

            if len(semantic_row) > 10:
                semantic_rows.append(semantic_row)

        return semantic_rows

    # =========================================================
    # 🔥 DETECT TABLE BOXES (HEAVY)
    # =========================================================
    def get_table_boxes(self, pdf_path: str):
        page_boxes = {}

        print(f"\n📦 [TABLE] Detecting tables in FULL PDF: {pdf_path}")
        start_total = time.time()

        try:
            with _camelot_lock:

                t0 = time.time()
                print("   ⏳ Running Camelot (lattice, ALL pages)...")
                tables = camelot.read_pdf(pdf_path, pages="all", flavor="lattice")
                print(f"   ✅ Lattice found {len(tables)} tables in {round(time.time() - t0, 2)}s")

                if len(tables) == 0:
                    t0 = time.time()
                    print("   ⏳ Running Camelot (stream fallback, ALL pages)...")
                    tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
                    print(f"   ✅ Stream found {len(tables)} tables in {round(time.time() - t0, 2)}s")

            for table in tables:
                page = table.page
                bbox = table._bbox

                if page not in page_boxes:
                    page_boxes[page] = []

                page_boxes[page].append(bbox)

        except Exception as e:
            print(f"❌ [TABLE] Failed detecting tables: {e}")

        print(f"📦 [TABLE] DONE table detection in {round(time.time() - start_total, 2)}s")

        return page_boxes

    # =========================================================
    # 🔥 EXTRACT TABLE TEXT PER PAGE (MAIN BOTTLENECK)
    # =========================================================
    def get_tables_text(self, pdf_path: str, page_number: int) -> List[str]:

        print(f"\n📊 [TABLE] Extracting tables → page {page_number}")

        table_sentences = []

        try:
            with _camelot_lock:

                t0 = time.time()
                print("   ⏳ Camelot lattice...")
                tables = camelot.read_pdf(pdf_path, pages=str(page_number), flavor="lattice")
                print(f"   ✅ Lattice tables: {len(tables)} in {round(time.time() - t0, 2)}s")

                if len(tables) == 0:
                    t0 = time.time()
                    print("   ⏳ Camelot stream fallback...")
                    tables = camelot.read_pdf(pdf_path, pages=str(page_number), flavor="stream")
                    print(f"   ✅ Stream tables: {len(tables)} in {round(time.time() - t0, 2)}s")

            if len(tables) == 0:
                print(f"   ⚠️ No tables found on page {page_number}")
                return []

            for table in tables:
                rows = self.table_to_semantic_text(table.df)
                table_sentences += rows

            print(f"   🧾 Extracted {len(table_sentences)} table rows")

            return table_sentences

        except Exception as e:
            print(f"❌ Table extraction failed on page {page_number}: {e}")
            return []

    # =========================================================
    # 🔥 WRAPPER
    # =========================================================
    def extract(self, pdf_path: str, page_number: int) -> List[str]:

        try:
            return self.get_tables_text(pdf_path, page_number)

        except Exception as e:
            print(f"❌ [TABLE] Unexpected error: {e}")
            return []