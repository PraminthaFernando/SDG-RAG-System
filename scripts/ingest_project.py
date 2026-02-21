import argparse
from ingestion.ingestion_pipeline import IngestionPipeline
from embeddings.embedding_factory import EmbeddingFactory
from vectordb.vector_store import VectorStore
from scripts.utils import setup_logger

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=str, required=True)
    parser.add_argument("--file", type=str, required=True)

    args = parser.parse_args()
    logger = setup_logger()

    logger.info(f"Ingesting project {args.pid}...")

    # Ingestion
    pipeline = IngestionPipeline(pdf_base_path="data/pdfs")
    document = pipeline.ingest(pid=args.pid, filename=args.file)

    # Embeddings + Vector Store
    embedding_model = EmbeddingFactory.create("e5", batch_size=32)
    vector_store = VectorStore(embedding_model)
    vector_store.initialize()

    docs_to_insert = []

    for i, page in enumerate(document.pages):
        docs_to_insert.append({
            "id": f"{args.pid}_{args.file}_{i}",
            "pid": args.pid,
            "document": args.file,
            "page_number": page.page,
            "chunk_number": i,
            "content": page.text
        })

    vector_store.insert_documents(docs_to_insert)

    logger.info(f"Inserted {len(docs_to_insert)} chunks.")


if __name__ == "__main__":
    main()