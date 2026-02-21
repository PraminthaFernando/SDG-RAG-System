from ingestion.ingestion_pipeline import IngestionPipeline
from embeddings.embedding_factory import EmbeddingFactory
from vectordb.vector_store import VectorStore
from .base_pipeline import BasePipeline
from .utils import setup_pipeline_logger

class ProjectIngestPipeline(BasePipeline):

    def __init__(self, pid: int, filename: str):
        self.pid = pid
        self.filename = filename
        self.logger = setup_pipeline_logger("IngestPipeline")

    def run(self):

        self.logger.info(f"Starting ingestion for PID {self.pid}")

        # 1. Ingestion
        ingestion = IngestionPipeline(pdf_base_path="data/pdfs")
        document = ingestion.ingest(pid=self.pid, filename=self.filename)

        # 2. Embeddings
        embedding_model = EmbeddingFactory.create("e5", batch_size=32)

        # 3. Vector store
        vector_store = VectorStore(embedding_model)
        vector_store.initialize()

        docs_to_insert = []

        for i, page in enumerate(document.pages):
            docs_to_insert.append({
                "id": f"{self.pid}_{self.filename}_{i}",
                "pid": self.pid,
                "document": self.filename,
                "page_number": page.page,
                "chunk_number": i,
                "content": page.text
            })

        vector_store.insert_documents(docs_to_insert)

        self.logger.info(f"Inserted {len(docs_to_insert)} chunks.")

        return {
            "pid": self.pid,
            "chunks_inserted": len(docs_to_insert)
        }