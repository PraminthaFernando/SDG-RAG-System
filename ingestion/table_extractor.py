import camelot
import threading
from typing import List
import warnings

warnings.filterwarnings("ignore", category=Warning)

_camelot_lock = threading.Lock()

class TableExtractor:
    
    def table_to_semantic_text(self, df) -> List[str]:
        headers = df.iloc[0]  # first row as header
        semantic_rows = []

        for i in range(1, len(df)):
            row = df.iloc[i]
            row_text_parts = []

            for col_index, cell in enumerate(row):
                header = headers[col_index].replace("\n", " ").strip()
                cell = str(cell).replace("\n", " ").strip()

                row_text_parts.append(f"{header}: {cell}")

            semantic_row = " | ".join(row_text_parts)
            # semantic_rows.append(semantic_row)
            if len(semantic_row) > 10:
                semantic_rows.append(semantic_row)

        return semantic_rows
    
    def get_tables_text(self, pdf_path : str, page_number : int) -> List[str]:
        table_sentences = []
        try:
            with _camelot_lock:
                tables = camelot.read_pdf(pdf_path, pages=str(page_number), flavor="lattice")
                if len(tables) == 0:
                    tables = camelot.read_pdf(pdf_path, pages=str(page_number), flavor="stream")
            
            if len(tables) == 0:
                return ""
            
            for table in tables:
                table_sentences += self.table_to_semantic_text(table.df)
            return table_sentences
        except Exception as e:
            print(f"Table extraction failed on page {page_number}: {e}")
            return ""

    def extract(self, pdf_path: str, page_number : int) -> List[str]:
        table_sentences = []

        try:
            table_sentences = self.get_tables_text(pdf_path, page_number)
        except Exception:
            pass
        finally:
            return table_sentences