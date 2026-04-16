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

# 🔥 DB IMPORTS
from RDS.database import SessionLocal
from RDS.crud_metadata import upsert_metadata
from RDS.crud_docs import replace_project_documents


# =========================================================
# 🔥 HELPER LOG
# =========================================================
def log_step(logger, msg):
    logger.info(f"⏱️ {msg} | {time.strftime('%H:%M:%S')}")


# =========================================================
# 🔥 METADATA FETCH
# =========================================================
def fetch_verra_metadata(pid: str, logger: Logger):
    try:
        numeric_id = pid.replace("VCS_", "")
        url = f"https://registry.verra.org/uiapi/resource/resourceSummary/{numeric_id}"

        logger.info(f"[{pid}] 🌐 Fetching metadata...")
        res = requests.get(url, timeout=30)
        res.raise_for_status()
        data = res.json()

        def get_attr(code):
            for p in data.get("participationSummaries", []):
                for attr in p.get("attributes", []):
                    if attr.get("code") == code:
                        return attr.get("values", [{}])[0].get("value")
            return None

        def to_int(val):
            try:
                return int(float(val)) if val else None
            except:
                return None

        metadata = {
            "project_id": pid,
            "project_name": data.get("resourceName") or "",
            "description": data.get("description") or "",
            "latitude": data.get("location", {}).get("latitude"),
            "longitude": data.get("location", {}).get("longitude"),
            "state_province": get_attr("STATE_PROVINCE") or "",
            "project_status": get_attr("PROJECT_STATUS") or "",
            "annual_emission_reduction": to_int(get_attr("EST_ANNUAL_EMISSION_REDCT")),
            "buffer_pool_credits": to_int(get_attr("TOTAL_BUFFER_POOL_CREDITS")),
            "project_category": get_attr("PRIMARY_PROJECT_CATEGORY_NAME") or "",
            "project_subcategory": get_attr("PROJECT_SUBCATERGORY_NAMES") or "",
            "registration_date": get_attr("PROJECT_REGISTRATION_DATE") or "",
            "crediting_period": get_attr("CREDIT_PERIOD_INFO") or ""
        }

        return metadata, data.get("documentGroups", [])

    except Exception as e:
        logger.error(f"[{pid}] ❌ Metadata fetch failed: {e}")
        return None, []


# =========================================================
# 🔥 EXTRACT DOCUMENTS
# =========================================================
def extract_documents(document_groups):
    docs = []
    for group in document_groups:
        for d in group.get("documents", []):
            docs.append({
                "documentName": d.get("documentName"),
                "documentType": d.get("documentType"),
                "uploadDate": d.get("uploadDate"),
                "uri": d.get("uri")
            })
    return docs


# =========================================================
# 🔥 FILTERING
# =========================================================
def classify_doc(doc):
    text = ((doc.get("documentName") or "") + " " +
            (doc.get("documentType") or "")).lower()

    if any(k in text for k in ["monitor", "mr"]):
        return "monitoring"
    if any(k in text for k in ["verif", "vr"]):
        return "verification"
    if any(k in text for k in ["proj", "pdd"]):
        return "description"
    if any(k in text for k in ["valid"]):
        return "validation"

    return "other"


def is_noise(doc):
    name = (doc.get("documentName") or "").lower()
    return any(k in name for k in ["draft", "summary", "kml", "agreement", "annex"])


def clean_and_group_docs(docs):
    grouped = {"monitoring": [], "verification": [], "description": [], "validation": []}

    for d in docs:
        if is_noise(d):
            continue

        cat = classify_doc(d)
        if cat in grouped:
            grouped[cat].append(d)

    return grouped


# =========================================================
# 🔥 PICK BEST DOC
# =========================================================
def pick_best_docs(grouped):
    selected = []

    def latest(docs):
        if not docs:
            return None
        return sorted(docs, key=lambda x: x.get("uploadDate", ""), reverse=True)[0]

    for key in ["monitoring", "verification", "description", "validation"]:
        doc = latest(grouped[key])
        if doc:
            selected.append(doc)

    return selected[:1]


# =========================================================
# 🔥 BULLETPROOF TEMP PROCESS
# =========================================================
def process_url_temp(doc, pid, pipeline):
    tmp_path = None

    try:
        url = doc["uri"]
        filename = doc["documentName"]

        res = requests.get(url, timeout=60)
        res.raise_for_status()

        tmp_path = os.path.join(
            tempfile.gettempdir(),
            f"{pid}_{int(time.time() * 1000)}.pdf"
        )

        with open(tmp_path, "wb") as f:
            f.write(res.content)

        time.sleep(0.05)

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

    # -------------------------
    # METADATA
    # -------------------------
    await send_update(proj, "Fetching metadata")
    metadata, document_groups = fetch_verra_metadata(proj, logger)

    await send_update(proj, "Metadata fetched")

    if metadata:
        db = SessionLocal()
        try:
            upsert_metadata(db, metadata)
        finally:
            db.close()

    # -------------------------
    # DOCUMENT SELECTION
    # -------------------------
    await send_update(proj, "Selecting best documents")

    docs = extract_documents(document_groups)
    grouped = clean_and_group_docs(docs)
    selected = pick_best_docs(grouped)

    # -------------------------
    # SAVE DOCS TO DB
    # -------------------------
    db = SessionLocal()
    try:
        replace_project_documents(db, proj, selected)
    finally:
        db.close()

    # -------------------------
    # PROCESSING
    # -------------------------
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

    # -------------------------
    # EMBEDDING
    # -------------------------
    await send_update(proj, "Generating embeddings")

    if all_docs:
        store.insert_documents(all_docs)

    await send_update(proj, "Stored in vector database")

    log_step(logger, f"[{proj}] ✅ DONE")


# =========================================================
# 🔥 CLI
# =========================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--workers", type=int, default=2)

    args = parser.parse_args()

    logger = setup_logger("ingestion")
    embedding = EmbeddingFactory.create("nomic", batch_size=32)

    store = VectorStore(embedding)

    # 🔥 THIS IS THE MISSING PIECE
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