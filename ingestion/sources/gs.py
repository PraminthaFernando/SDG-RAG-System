from logging import Logger
import requests
import asyncio


# =========================================================
# 🔥 SAFE UPDATE (FOR WEBSOCKET)
# =========================================================
def safe_update(send_update, pid, msg):
    if not send_update:
        return
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(send_update(pid, msg), loop)
        else:
            asyncio.run(send_update(pid, msg))
    except:
        pass


# =========================================================
# 🔥 COMMON HEADERS (CRITICAL FOR GS API)
# =========================================================
def get_headers():
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://registry.goldstandard.org",
        "referer": "https://registry.goldstandard.org/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/147 Safari/537.36",
    }


# =========================================================
# 🔥 FETCH GS METADATA
# =========================================================
def fetch_gs_metadata(pid: str, logger: Logger):
    try:
        numeric_id = pid.replace("GS_", "").replace("GS", "")
        url = f"https://public-api.goldstandard.org/projects/{numeric_id}"

        logger.info(f"[{pid}] 🌐 Fetching GS metadata...")

        res = requests.get(url, headers=get_headers(), timeout=30)
        res.raise_for_status()
        data = res.json()

        metadata = {
            "project_id": pid,

            "gs_project_numeric_id": numeric_id,
            "sustaincert_id": data.get("sustaincert_id"),
            "sustaincert_url": data.get("sustaincert_url"),

            "project_name": data.get("name"),
            "description": data.get("description"),

            "project_status": data.get("status"),
            "standard": data.get("gsf_standards_version"),

            "project_type": data.get("type"),
            "project_size": data.get("size"),
            "methodology": data.get("methodology"),

            "project_developer": data.get("project_developer"),
            "country": data.get("country"),
            "country_code": data.get("country_code"),
            "state": data.get("state"),

            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),

            "annual_credits": data.get("estimated_annual_credits"),
            "carbon_stream": data.get("carbon_stream"),

            "crediting_start_date": data.get("crediting_period_start_date"),
            "crediting_end_date": data.get("crediting_period_end_date"),

            "programme_of_activities": data.get("programme_of_activities"),
            "poa_project_id": data.get("poa_project_id"),
            "poa_project_sustaincert_id": data.get("poa_project_sustaincert_id"),

            "corsia_eligible": data.get("has_corsia_eligible_credits"),

            "sdgs": data.get("sustainable_development_goals"),
        }

        gsid = data.get("sustaincert_id")

        return metadata, gsid

    except Exception as e:
        logger.error(f"[{pid}] ❌ GS metadata fetch failed: {e}")
        return None, None


# =========================================================
# 🔥 FETCH GS DOCUMENTS
# =========================================================
def fetch_gs_documents(gsid: str, logger: Logger):
    try:
        url = f"https://assurance-platform.goldstandard.org/api/public/project-documents/GS{gsid}"

        logger.info(f"[GS{gsid}] 📄 Fetching GS documents...")

        headers = {
            **get_headers(),
            "accept": "*/*",
            "referer": f"https://assurance-platform.goldstandard.org/project-documents/GS{gsid}",
            "x-gold-standard-api-version": "2023-04-19"
        }

        res = requests.get(url, headers=headers, timeout=30)
        res.raise_for_status()

        return res.json()

    except Exception as e:
        logger.error(f"[GS{gsid}] ❌ GS document fetch failed: {e}")
        return None


# =========================================================
# 🔥 EXTRACT DOCUMENTS
# =========================================================
def extract_documents(gs_data):
    docs = []

    if not gs_data:
        return docs

    for req in gs_data.get("requests", []):
        for d in req.get("documents", []):

            filename = d.get("filename", "")

            if not filename.lower().endswith(".pdf"):
                continue

            doc_id = d.get("id")

            download_url = f"https://assurance-platform.goldstandard.org/api/public/documents/{doc_id}/download"

            docs.append({
                "documentName": filename,
                "documentType": req.get("requestType", ""),
                "uploadDate": d.get("uploadedTimestamp"),
                "uri": download_url
            })

    return docs


# =========================================================
# 🔥 CLASSIFICATION
# =========================================================
def classify_doc(doc):
    text = ((doc.get("documentName") or "") + " " +
            (doc.get("documentType") or "")).lower()

    if any(k in text for k in ["performance review", "monitor", "mr"]):
        return "monitoring"

    if any(k in text for k in ["verif", "verification"]):
        return "verification"

    if any(k in text for k in ["design", "project", "pdd"]):
        return "description"

    if any(k in text for k in ["valid"]):
        return "validation"

    return "other"


def is_noise(doc):
    name = (doc.get("documentName") or "").lower()

    return any(k in name for k in [
        "draft", "summary", "kml", "agreement", "annex"
    ])


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

        cat = classify_doc(d)

        if cat in grouped:
            grouped[cat].append(d)

    return grouped


# =========================================================
# 🔥 SMART SELECTION (TOP DOCS)
# =========================================================
def pick_best_docs(grouped):
    all_docs = []

    for docs in grouped.values():
        all_docs.extend(docs)

    def score(doc):
        text = ((doc.get("documentName") or "") + " " +
                (doc.get("documentType") or "")).lower()

        score = 0

        category = classify_doc(doc)
        if category == "monitoring":
            score += 5
        elif category == "verification":
            score += 4
        elif category == "description":
            score += 2
        elif category == "validation":
            score += 1

        keywords = [
            "sdg", "impact", "sustainable",
            "monitoring", "performance",
            "verification", "report",
            "emission", "benefit", "outcome"
        ]

        for k in keywords:
            if k in text:
                score += 1

        if doc.get("uploadDate"):
            score += 1

        return score

    ranked = sorted(all_docs, key=score, reverse=True)

    return ranked[:2]   # 🔥 adjust if needed


# =========================================================
# 🔥 MAIN ENTRY FUNCTION (UPDATED WITH PROGRESS)
# =========================================================
def process_gs_project(pid: str, logger: Logger, send_update=None):

    safe_update(send_update, pid, "Fetching GS metadata")

    metadata, gsid = fetch_gs_metadata(pid, logger)

    if not gsid:
        return metadata, []

    safe_update(send_update, pid, "Fetching GS documents")

    gs_docs_data = fetch_gs_documents(gsid, logger)

    safe_update(send_update, pid, "Extracting documents")

    docs = extract_documents(gs_docs_data)

    safe_update(send_update, pid, f"Found {len(docs)} documents")

    grouped = clean_and_group_docs(docs)

    safe_update(send_update, pid, "Ranking documents")

    selected = pick_best_docs(grouped)

    safe_update(send_update, pid, f"Selected {len(selected)} documents")

    return metadata, selected