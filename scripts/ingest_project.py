from logging import Logger
import os
import argparse
import json
import requests
import time
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

from ingestion.ingestion_pipeline import IngestionPipeline
from embeddings.embedding_factory import EmbeddingFactory
from vectordb.vector_store import VectorStore
from scripts.utils import setup_logger

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
            "project_id": numeric_id,
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
# 🔥 SAVE METADATA
# =========================================================
def save_metadata(pid: str, metadata: dict):
    out_dir = Path("outputs") / pid
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)


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
# 🔥 SMART FILTER
# =========================================================
def classify_doc(doc):
    text = ((doc.get("documentName") or "") + " " +
            (doc.get("documentType") or "")).lower()

    if any(k in text for k in ["monitor", "monit", "mr"]):
        return "monitoring"
    if any(k in text for k in ["verif", "verification", "vr"]):
        return "verification"
    if any(k in text for k in ["proj", "description", "pdd"]):
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
# 🔥 PICK BEST DOCS
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
# 🔥 DOWNLOAD PDFs
# =========================================================
async def download_documents(pid, docs, send_update):
    pdf_dir = Path("pdfs") / pid
    pdf_dir.mkdir(parents=True, exist_ok=True)

    for i, d in enumerate(docs, 1):
        filename = d["documentName"]

        await send_update(pid, f"Downloading {i}/{len(docs)}: {filename}")

        try:
            res = requests.get(d["uri"], timeout=60)
            res.raise_for_status()

            with open(pdf_dir / filename, "wb") as f:
                f.write(res.content)

        except Exception as e:
            print(f"[{pid}] ❌ Download failed: {e}")


# =========================================================
# 🔥 PROCESS FILE
# =========================================================
def process_file(filename, pid, pipeline):
    try:
        document = pipeline.ingest(pid=pid, filename=filename)

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

    except Exception:
        return []


# =========================================================
# 🔥 MAIN PIPELINE (REAL-TIME)
# =========================================================
async def process_project_with_progress(base_path, proj, workers, logger, store, send_update):

    log_step(logger, f"[{proj}] 🚀 START")

    project_path = base_path / proj
    project_path.mkdir(parents=True, exist_ok=True)

    pipeline = IngestionPipeline(pdf_base_path=str(project_path))

    # 🔥 METADATA
    await send_update(proj, "Fetching metadata")
    metadata, document_groups = fetch_verra_metadata(proj, logger)

    await send_update(proj, "Metadata fetched")

    if metadata:
        save_metadata(proj, metadata)

    # 🔥 CHECK PDFs
    pdf_files = [f for f in os.listdir(project_path) if f.endswith(".pdf")]

    if not pdf_files:
        await send_update(proj, "Selecting best documents")

        docs = extract_documents(document_groups)
        grouped = clean_and_group_docs(docs)
        selected = pick_best_docs(grouped)

        await send_update(proj, f"Downloading {len(selected)} PDFs")
        await download_documents(proj, selected, send_update)

        pdf_files = [f for f in os.listdir(project_path) if f.endswith(".pdf")]

    # 🔥 PROCESSING
    await send_update(proj, f"Processing {len(pdf_files)} PDFs")

    all_docs = []
    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        tasks = [
            loop.run_in_executor(executor, process_file, f, proj, pipeline)
            for f in pdf_files
        ]

        for i, future in enumerate(asyncio.as_completed(tasks), 1):
            result = await future
            all_docs.extend(result)

            await send_update(proj, f"Processed {i}/{len(pdf_files)} PDFs")

    await send_update(proj, f"Extracted {len(all_docs)} chunks")

    # 🔥 EMBEDDING
    await send_update(proj, "Generating embeddings")

    if all_docs:
        store.insert_documents(all_docs)

    await send_update(proj, "Stored in vector database")

    log_step(logger, f"[{proj}] ✅ DONE")


# =========================================================
# 🔥 CLI (UNCHANGED)
# =========================================================
def main():
    parser = argparse.ArgumentParser(description="Single project ingest")
    parser.add_argument("--path", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--reset", action="store_true")

    args = parser.parse_args()
    logger = setup_logger("IngestProject")

    embedding_model = EmbeddingFactory.create("nomic", batch_size=args.batch_size)

    vector_store = VectorStore(embedding_model)
    vector_store.initialize(args.reset, model="nomic", collection="nomic")

    asyncio.run(
        process_project_with_progress(
            Path(args.path),
            args.project,
            args.workers,
            logger,
            vector_store,
            lambda pid, msg: print(f"[{pid}] {msg}")
        )
    )


if __name__ == "__main__":
    main()