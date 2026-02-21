from logging import Logger
import os
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from ingestion.ingestion_pipeline import IngestionPipeline
from embeddings.embedding_factory import EmbeddingFactory
from vectordb.vector_store import VectorStore
from scripts.utils import setup_logger

def process_file(filename : str, pid : str, pipeline : IngestionPipeline, logger : Logger):
    """
    Process single PDF file:
    - Ingest
    - Chunk
    - Prepare docs for insertion
    Returns prepared document dict list
    """

    try:
        logger.info(f"Processing {filename}")

        document = pipeline.ingest(pid=pid, filename=filename)

        docs_to_insert = []

        for i, page in enumerate(document.pages):
            docs_to_insert.append({
                "id": f"{pid}_{filename}_{i}",
                "pid": pid,
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

def process_project(path : Path, proj : str, workers : int, logger : Logger, store) -> list:
    all_docs = []
    project_path = path / proj
    base_path = Path(project_path)
    pipeline = IngestionPipeline(pdf_base_path=str(base_path))
    pdf_files = [
        f for f in os.listdir(project_path)
        if f.lower().endswith(".pdf")
    ]
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(process_file, f, proj, pipeline, logger)
            for f in pdf_files
        ]

        for future in as_completed(futures):
            result = future.result()
            all_docs.extend(result)
            
    logger.info(f"Total chunks prepared for store: {len(all_docs)}")

    if not all_docs:
        logger.warning("No documents prepared. Exiting.")
        return []
    
    store.insert_documents(all_docs)
          
    return all_docs
    

def main():
    parser = argparse.ArgumentParser(
        description="Threaded batch ingest for project folder"
    )

    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--reset", type=bool, default=False)

    args = parser.parse_args()
    logger = setup_logger("BatchIngest")

    if not os.path.isdir(args.path):
        logger.error(f"Invalid directory: {args.path}")
        return

    logger.info(f"Starting batch ingestion from: {args.path}")

    # pipeline = IngestionPipeline(pdf_base_path=args.path)
    embedding_model = EmbeddingFactory.create("remort", api_url="https://inadvertently-measureless-ester.ngrok-free.dev")
    vector_store = VectorStore(embedding_model)
    vector_store.initialize(args.reset)

    # all_projects = []
    
    projects = [
        proj for proj in os.listdir(args.path)
    ]

    logger.info(f"Using {args.workers} worker threads")
    
    insert_count = 0

    # -----------------------------------
    # Parallel ingestion (safe)
    # -----------------------------------
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(process_project, Path(args.path), proj, args.workers, logger, vector_store)
            for proj in projects[:40]
        ]

        for future in as_completed(futures):
            result = future.result()
            # all_projects.extend(result)
            # vector_store.insert_documents(result)
            insert_count += 1
            logger.info(f"Number of rojects stored: {insert_count}")
            

    logger.info(f"Total projects stored: {insert_count}")

    # if not all_projects:
    #     logger.warning("No projects prepared. Exiting.")
    #     return

    # -----------------------------------
    # Embedding + Insert (single-threaded)
    # -----------------------------------
    # logger.info("Starting embedding + vector insertion")

    # vector_store.insert_documents(all_projects)

    # logger.info("Batch ingestion complete.")
    # logger.info(f"Total chunks inserted: {len(all_projects)}")


if __name__ == "__main__":
    main()