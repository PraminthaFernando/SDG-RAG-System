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

from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# =========================================================
# 🔥 HELPER LOG
# =========================================================
def log_step(logger, msg):
    logger.info(f"⏱️ {msg} | {time.strftime('%H:%M:%S')}")

# =========================================================
# 🔥 METADATA FETCH + CLEAN TRANSFORM
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

        logger.info(f"[{pid}] ✅ Metadata ready")

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

    logger.info(f"[{pid}] 💾 Metadata saved")

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
# 🔥 LLM DOCUMENT SELECTION
# =========================================================
def select_top_documents_llm(docs, logger):
    try:
        logger.info("🤖 Calling LLM for document selection")

        doc_text = "\n".join([
            f"{i}. {d['documentName']} | {d['documentType']} | {d['uploadDate']}"
            for i, d in enumerate(docs)
        ])

        prompt = f"""
Select TOP 5 documents most useful for SDG co-benefit evidence.

Prioritize:
- Monitoring Reports
- Verification Reports
- Project Description

Return ONLY JSON list of indices.

Documents:
{doc_text}
"""

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        content = response.choices[0].message.content.strip()
        indices = json.loads(content)

        selected = [docs[i] for i in indices if i < len(docs)]

        logger.info(f"✅ LLM selected {len(selected)} documents")

        return selected[:5]

    except Exception as e:
        logger.error(f"❌ LLM failed → fallback: {e}")
        return fallback_selection(docs)

# =========================================================
# 🔥 FALLBACK
# =========================================================
def fallback_selection(docs):
    keywords = ["monitor", "report", "verification", "project"]
    scored = []

    for d in docs:
        name = (d.get("documentName") or "").lower()
        score = sum(k in name for k in keywords)
        scored.append((score, d))

    scored.sort(reverse=True)
    return [d for _, d in scored[:5]]

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

            logger.info(f"[{pid}] ⬇️ Downloading {filename}")

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
        logger.info(f"[{pid}] 📄 Processing {filename}")

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

        logger.info(f"[{pid}] ✅ {filename} → {len(docs_to_insert)} chunks")

        return docs_to_insert

    except Exception as e:
        logger.error(f"[{pid}] ❌ Failed on {filename}: {e}")
        return []

# =========================================================
# 🔥 PROCESS PROJECT
# =========================================================
def process_project(path: Path, proj: str, workers: int, logger: Logger, store):

    log_step(logger, f"[{proj}] 🚀 START PROJECT")

    project_path = path / proj
    pipeline = IngestionPipeline(pdf_base_path=str(project_path))

    metadata, document_groups = fetch_verra_metadata(proj, logger)

    if metadata:
        save_metadata(proj, metadata, logger)

    pdf_files = [
        f for f in os.listdir(project_path)
        if f.lower().endswith(".pdf")
    ]

    logger.info(f"[{proj}] 📄 Found {len(pdf_files)} PDFs")

    if not pdf_files:
        logger.info(f"[{proj}] ⬇️ No PDFs → downloading")

        docs = extract_documents(document_groups)

        if docs:
            selected_docs = select_top_documents_llm(docs, logger)
            download_documents(proj, selected_docs, logger)

        pdf_files = [
            f for f in os.listdir(project_path)
            if f.lower().endswith(".pdf")
        ]

        logger.info(f"[{proj}] 📄 After download → {len(pdf_files)} PDFs")

    log_step(logger, f"[{proj}] 🧠 Starting ingestion")

    all_docs = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(process_file, f, proj, pipeline, logger)
            for f in pdf_files
        ]

        for future in as_completed(futures):
            all_docs.extend(future.result())

    logger.info(f"[{proj}] 🧾 Total chunks: {len(all_docs)}")

    log_step(logger, f"[{proj}] 💾 Inserting into vector DB")

    BATCH_SIZE = 500

    if not all_docs:
        logger.warning(f"[{proj}] No documents to insert")
        return []

    if len(all_docs) > BATCH_SIZE:
        for i in range(0, len(all_docs), BATCH_SIZE):
            batch = all_docs[i:i + BATCH_SIZE]
            store.insert_documents(batch)
    else:
        store.insert_documents(all_docs)

    log_step(logger, f"[{proj}] ✅ DONE")

    return all_docs

# =========================================================
# 🔥 MAIN
# =========================================================
def main():
    parser = argparse.ArgumentParser(description="Batch ingest")
    parser.add_argument("--path", required=True)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--reset", type=bool, default=False)

    args = parser.parse_args()
    logger = setup_logger("BatchIngest")

    log_step(logger, "🚀 Script started")

    if not os.path.isdir(args.path):
        logger.error("Invalid path")
        return

    log_step(logger, "🔧 Loading embedding model")
    start = time.time()

    embedding_model = EmbeddingFactory.create("nomic", batch_size=args.batch_size)

    log_step(logger, f"✅ Embedding ready in {round(time.time() - start, 2)}s")

    log_step(logger, "🗄️ Connecting to Milvus")
    start = time.time()

    vector_store = VectorStore(embedding_model)
    vector_store.initialize(args.reset, model="nomic", collection="nomic")

    log_step(logger, f"✅ Milvus ready in {round(time.time() - start, 2)}s")

    projects = os.listdir(args.path)

    logger.info(f"📁 Found {len(projects)} projects")

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(process_project, Path(args.path), proj, args.workers, logger, vector_store)
            for proj in projects
        ]

        for i, future in enumerate(as_completed(futures), 1):
            future.result()
            logger.info(f"✅ Project completed ({i}/{len(projects)})")

    logger.info("🎉 All projects processed")


if __name__ == "__main__":
    main()