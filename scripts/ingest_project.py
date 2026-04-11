from logging import Logger
import os
import argparse
import json
import requests
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
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
def save_metadata(pid: str, metadata: dict, logger: Logger):
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
# 🔥 SMART DOCUMENT FILTERING
# =========================================================
def classify_doc(doc):
    name = (doc.get("documentName") or "").lower()
    dtype = (doc.get("documentType") or "").lower()

    text = name + " " + dtype

    if any(k in text for k in ["monitor", "monit", "mr"]):
        return "monitoring"

    if any(k in text for k in ["verif", "verification", "vr"]):
        return "verification"

    if any(k in text for k in ["proj_desc", "project description", "pdd"]):
        return "description"

    if any(k in text for k in ["valid", "validation"]):
        return "validation"

    return "other"

def is_noise(doc):
    name = (doc.get("documentName") or "").lower()

    bad_keywords = [
        "draft", "summary", "kml", "agreement",
        "annex", "communication", "template"
    ]

    return any(k in name for k in bad_keywords)

def clean_and_group_docs(docs):
    grouped = {
        "monitoring": [],
        "verification": [],
        "description": [],
        "validation": []
    }

    for d in docs:
        if is_noise(d):
            continue

        category = classify_doc(d)

        if category in grouped:
            grouped[category].append(d)

    return grouped

# =========================================================
# 🔥 PICK BEST DOCS
# =========================================================
def pick_best_docs(grouped, logger):
    selected = []

    def pick_latest(docs):
        if not docs:
            return None
        return sorted(docs, key=lambda x: x.get("uploadDate", ""), reverse=True)[0]

    # Always prioritize these
    for key in ["monitoring", "verification", "description", "validation"]:
        doc = pick_latest(grouped[key])
        if doc:
            selected.append(doc)

    logger.info(f"📄 Selected {len(selected)} high-quality documents")

    return selected[:5]

# =========================================================
# 🔥 DOWNLOAD PDFs
# =========================================================
def download_documents(pid: str, docs, logger: Logger):
    pdf_dir = Path("pdfs") / pid
    pdf_dir.mkdir(parents=True, exist_ok=True)

    for d in docs:
        try:
            url = d["uri"]
            filename = d["documentName"]

            logger.info(f"[{pid}] ⬇️ {filename}")

            res = requests.get(url, timeout=60)
            res.raise_for_status()

            with open(pdf_dir / filename, "wb") as f:
                f.write(res.content)

        except Exception as e:
            logger.error(f"[{pid}] ❌ Download failed: {e}")

# =========================================================
# 🔥 PROCESS FILE
# =========================================================
def process_file(filename: str, pid: str, pipeline: IngestionPipeline, logger: Logger):
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

    except Exception as e:
        logger.error(f"[{pid}] ❌ Failed on {filename}: {e}")
        return []

# =========================================================
# 🔥 MAIN PROCESS
# =========================================================
def process_project(base_path: Path, proj: str, workers: int, logger: Logger, store):

    log_step(logger, f"[{proj}] 🚀 START")

    project_path = base_path / proj
    project_path.mkdir(parents=True, exist_ok=True)

    pipeline = IngestionPipeline(pdf_base_path=str(project_path))

    metadata, document_groups = fetch_verra_metadata(proj, logger)

    if metadata:
        save_metadata(proj, metadata, logger)

    pdf_files = [f for f in os.listdir(project_path) if f.lower().endswith(".pdf")]

    if not pdf_files:
        logger.info(f"[{proj}] No PDFs → smart selecting + downloading")

        docs = extract_documents(document_groups)
        grouped = clean_and_group_docs(docs)
        selected = pick_best_docs(grouped, logger)

        download_documents(proj, selected, logger)

        pdf_files = [f for f in os.listdir(project_path) if f.lower().endswith(".pdf")]

    logger.info(f"[{proj}] PDFs found: {len(pdf_files)}")

    all_docs = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(process_file, f, proj, pipeline, logger)
            for f in pdf_files
        ]

        for future in as_completed(futures):
            all_docs.extend(future.result())

    logger.info(f"[{proj}] Total chunks: {len(all_docs)}")

    if all_docs:
        store.insert_documents(all_docs)

    log_step(logger, f"[{proj}] ✅ DONE")

# =========================================================
# 🔥 MAIN
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

    log_step(logger, "🚀 Script started")

    embedding_model = EmbeddingFactory.create("nomic", batch_size=args.batch_size)

    vector_store = VectorStore(embedding_model)
    vector_store.initialize(args.reset, model="nomic", collection="nomic")

    process_project(
        Path(args.path),
        args.project,
        args.workers,
        logger,
        vector_store
    )

    logger.info("🎉 Done")

if __name__ == "__main__":
    main()