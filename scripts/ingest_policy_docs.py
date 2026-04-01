# scripts/ingest_policy_docs.py
from logging import Logger
import os
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from ingestion.ingestion_pipeline import IngestionPipeline
from embeddings.embedding_factory import EmbeddingFactory
from vectordb.vector_store import VectorStore
from scripts.utils import setup_logger

def process_file(filename : str, pipeline : IngestionPipeline, logger : Logger):
    """
    Process single PDF file:
    - Ingest
    - Chunk
    - Prepare docs for insertion
    Returns prepared document dict list
    """

    try:
        logger.info(f"Processing {filename}")

        document = pipeline.ingest(pid=None, filename=filename)

        docs_to_insert = []

        for i, page in enumerate(document.pages):
            docs_to_insert.append({
                "id": f"{filename}_{i}",
                "document": filename,
                "page_number": page.page,
                "chunk_number": i,
                "content": page.text
            })

        logger.info(f"{filename}: Prepared {len(docs_to_insert)} chunks")

        return docs_to_insert

    except Exception as e:
        logger.error(f"Failed on {filename}: {str(e)}")
        return []

def main():
    parser = argparse.ArgumentParser(
        description="Threaded batch ingest for project folder"
    )

    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--reset", type=bool, default=False)

    args = parser.parse_args()
    logger = setup_logger("BatchIngest")

    if not os.path.isdir(args.path):
        logger.error(f"Invalid directory: {args.path}")
        return

    logger.info(f"Starting batch ingestion from: {args.path}")

    pipeline = IngestionPipeline(pdf_base_path=args.path)
    embedding_model = EmbeddingFactory.create("nomic", batch_size=args.batch_size)

    vector_store = VectorStore(embedding_model)
    vector_store.initialize(reset=args.reset, model="nomic", collection="policy_docs")

    all_docs = []

    pdf_files = [
        f for f in os.listdir(args.path)
        if f.lower().endswith(".pdf")
    ]

    logger.info(f"Found {len(pdf_files)} PDF files")
    logger.info(f"Using {args.workers} worker threads")
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(process_file, f, pipeline, logger)
            for f in pdf_files
        ]

        for future in as_completed(futures):
            result = future.result()
            all_docs.extend(result)

    logger.info(f"Total chunks prepared: {len(all_docs)}")

    BATCH_SIZE = 500

    if not all_docs:
        logger.warning("No documents prepared. Exiting.")
        return []

    total_docs = len(all_docs)
    logger.info(f"Preparing to insert {total_docs} documents")

    if total_docs > BATCH_SIZE:
        logger.info(f"Batch inserting documents (batch_size={BATCH_SIZE})")

        for start in range(0, total_docs, BATCH_SIZE):
            batch = all_docs[start:start + BATCH_SIZE]

            logger.info(
                f"Inserting batch {start // BATCH_SIZE + 1} "
                f"({start} - {start + len(batch)})"
            )

            vector_store.insert_documents(documents=batch, policy_docs=True)

    else:
        logger.info("Inserting documents in a single batch")
        vector_store.insert_documents(documents=all_docs, policy_docs=True)

    logger.info("Batch ingestion complete.")
    logger.info(f"Total chunks inserted: {len(all_docs)}")


if __name__ == "__main__":
    main()