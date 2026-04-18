from logging import Logger
import requests


# =========================================================
# 🔥 FETCH VERRA METADATA
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
# 🔥 CLASSIFICATION
# =========================================================
def classify_doc(doc):
    text = ((doc.get("documentName") or "") + " " +
            (doc.get("documentType") or "")).lower()

    if any(k in text for k in ["monitor", "mr", "monitoring"]):
        return "monitoring"

    if any(k in text for k in ["verif", "vr", "verification"]):
        return "verification"

    if any(k in text for k in ["proj", "pdd", "design"]):
        return "description"

    if any(k in text for k in ["valid"]):
        return "validation"

    return "other"


def is_noise(doc):
    name = (doc.get("documentName") or "").lower()

    return any(k in name for k in [
        "draft",
        "summary",
        "kml",
        "agreement",
        "annex"
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
# 🔥 SMART RANKING (TOP 5)
# =========================================================
def pick_best_docs(grouped):
    all_docs = []

    for docs in grouped.values():
        all_docs.extend(docs)

    def score(doc):
        text = ((doc.get("documentName") or "") + " " +
                (doc.get("documentType") or "")).lower()

        score = 0

        # 🔥 CATEGORY PRIORITY
        category = classify_doc(doc)
        if category == "monitoring":
            score += 5
        elif category == "verification":
            score += 4
        elif category == "description":
            score += 2
        elif category == "validation":
            score += 1

        # 🔥 SDG / IMPACT KEYWORDS
        keywords = [
            "sdg", "impact", "sustainable",
            "monitoring", "report", "verification",
            "emission", "benefit", "outcome"
        ]

        for k in keywords:
            if k in text:
                score += 1

        # 🔥 RECENCY BONUS
        if doc.get("uploadDate"):
            score += 1

        return score

    ranked = sorted(all_docs, key=score, reverse=True)

    return ranked[:2]   # 🔥 TOP 5


# =========================================================
# 🔥 MAIN ENTRY FUNCTION
# =========================================================
def process_verra_project(pid: str, logger: Logger):

    metadata, document_groups = fetch_verra_metadata(pid, logger)

    docs = extract_documents(document_groups)
    grouped = clean_and_group_docs(docs)
    selected = pick_best_docs(grouped)

    return metadata, selected