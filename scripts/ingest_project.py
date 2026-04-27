from logging import Logger
import argparse
import requests
import time
import asyncio
import os
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

from ingestion.ingestion_pipeline import IngestionPipeline
from embeddings.embedding_factory import EmbeddingFactory
from vectordb.vector_store import VectorStore
from scripts.utils import setup_logger

# 🔥 SOURCES
from ingestion.sources.verra import process_verra_project
from ingestion.sources.gs import process_gs_project

# 🔥 DB
from RDS.database import SessionLocal
from RDS.crud_docs import replace_project_documents


# =========================================================
# 🔥 HELPER LOG
# =========================================================
def log_step(logger, msg):
    logger.info(f"⏱️ {msg} | {time.strftime('%H:%M:%S')}")


# =========================================================
# 🔥 DOWNLOAD + PROCESS PDF (SOURCE-AWARE FIX)
# =========================================================
def process_url_temp(doc, pid, pipeline):
    tmp_path = None

    try:
        url = doc["uri"]
        filename = doc["documentName"]

        # 🔥 SOURCE-AWARE HEADERS
        if "goldstandard" in url:
            headers = {
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "referer": f"https://assurance-platform.goldstandard.org/project-documents/{pid.replace('_','')}",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/147 Safari/537.36",
                "x-gold-standard-api-version": "2023-04-19"
            }
        else:
            headers = {}

        res = requests.get(url, headers=headers, timeout=60)

        # 🔥 HANDLE BLOCKED DOCS
        if res.status_code == 403:
            print(f"[{pid}] ⚠️ Skipping restricted document: {filename}")
            return []

        res.raise_for_status()

        # 🔥 SAVE TEMP FILE
        tmp_path = os.path.join(
            tempfile.gettempdir(),
            f"{pid}_{int(time.time() * 1000)}.pdf"
        )

        with open(tmp_path, "wb") as f:
            f.write(res.content)

        time.sleep(0.05)

        # 🔥 INGEST
        document = pipeline.ingest(pid=pid, filename=tmp_path)

        return [
            {
                "id": f"{pid}_{filename}_{i}",
                "pid": pid,
                "document": filename,
                "page_number": page.page,
                "chunk_number": i,
                "content": page.text
            }
            for i, page in enumerate(document.pages)
        ]

    except Exception as e:
        print(f"[{pid}] ❌ Temp processing failed: {e}")
        return []

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass


# =========================================================
# 🔥 MAIN PIPELINE
# =========================================================
async def process_project_with_progress(base_path, proj, workers, logger, store, send_update):

    log_step(logger, f"[{proj}] 🚀 START")

    pipeline = IngestionPipeline(pdf_base_path=tempfile.gettempdir())

    # =========================================================
    # 🔥 FETCH SOURCE DATA
    # =========================================================
    await send_update(proj, "Fetching metadata")

    if proj.startswith("VCS"):
        metadata, selected = process_verra_project(proj, logger)
        source = "verra"

    elif proj.startswith("GS"):
        # 🔥 FIX: PASS send_update
        metadata, selected = process_gs_project(proj, logger, send_update)
        source = "gs"

    else:
        raise ValueError(f"Unknown project type: {proj}")

    await send_update(proj, "Metadata fetched")

    # =========================================================
    # 🔥 SAVE METADATA
    # =========================================================
    if metadata:
        db = SessionLocal()
        try:
            if source == "verra":
                from RDS.crud_metadata import upsert_metadata
                upsert_metadata(db, metadata)

            elif source == "gs":
                from RDS.crud_metadata_gs import upsert_metadata_gs
                upsert_metadata_gs(db, metadata)

        finally:
            db.close()

    # =========================================================
    # 🔥 SAVE DOCUMENTS
    # =========================================================
    await send_update(proj, "Saving selected documents")

    db = SessionLocal()
    try:
        replace_project_documents(db, proj, selected)
    finally:
        db.close()

    # =========================================================
    # 🔥 PROCESS PDFs
    # =========================================================
    await send_update(proj, f"Processing {len(selected)} PDFs")

    all_docs = []
    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        tasks = [
            loop.run_in_executor(executor, process_url_temp, d, proj, pipeline)
            for d in selected
        ]

        for i, future in enumerate(asyncio.as_completed(tasks), 1):
            result = await future
            all_docs.extend(result)

            await send_update(proj, f"Processed {i}/{len(selected)} PDFs")

    await send_update(proj, f"Extracted {len(all_docs)} chunks")

    # =========================================================
    # 🔥 EMBEDDINGS
    # =========================================================
    await send_update(proj, "Generating embeddings")

    if all_docs:
        store.insert_documents(all_docs)

    await send_update(proj, "Stored in vector database")

    log_step(logger, f"[{proj}] ✅ DONE")


# =========================================================
# 🔥 CLI
# =========================================================
if __name__ == "__main__":
    print("STARTING SCRIPT")
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--workers", type=int, default=2)

    args = parser.parse_args()

    logger = setup_logger("ingestion")
    embedding = EmbeddingFactory.create("nomic", batch_size=32)

    store = VectorStore(embedding)

    store.initialize(
        reset=False,
        model="nomic",
        collection="nomic"
    )

    async def send_update(pid, msg):
        print(f"[{pid}] {msg}")

    asyncio.run(
        process_project_with_progress(
            base_path=None,
            proj=args.project,
            workers=args.workers,
            logger=logger,
            store=store,
            send_update=send_update
        )
    )