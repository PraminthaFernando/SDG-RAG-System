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


# =========================================================
# 🔥 CLEAN + GROUP
# =========================================================
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
# 🔥 KEYWORD FILTER
# =========================================================
def keyword_filter_top20(docs):
    keywords = [
        "monitor", "monitoring",
        "verification", "verif", "vr",
        "pdd", "project description",
        "sdg", "impact", "report",
        "emission", "benefit"
    ]

    def score(doc):
        text = ((doc.get("documentName") or "") + " " +
                (doc.get("documentType") or "")).lower()
        return sum(1 for k in keywords if k in text)

    ranked = sorted(docs, key=score, reverse=True)
    return ranked[:20]


# =========================================================
# 🔥 LLM DOC SELECTOR (STRICT FIXED)
# =========================================================
def llm_select_best_docs(docs, logger: Logger, top_k=4):
    try:
        from llm.llm_client import GroqLLMClient
        import json
        import re

        client = GroqLLMClient()

        doc_list = [
            {"name": d.get("documentName"), "date": d.get("uploadDate")}
            for d in docs
        ]

        prompt = f"""
Select EXACTLY {top_k} best documents for SDG analysis.

Documents:
{doc_list}

Return ONLY JSON list of EXACTLY {top_k} names.
"""

        response = client.invoke(prompt)

        if not response or not response.strip():
            return docs[:top_k]

        cleaned = response.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1].replace("json", "").strip()

        try:
            selected_names = json.loads(cleaned)
        except:
            match = re.search(r"\[.*\]", cleaned, re.DOTALL)
            if match:
                selected_names = json.loads(match.group(0))
            else:
                return docs[:top_k]

        # 🔥 STRICT MATCH
        selected = []
        seen = set()

        for name in selected_names:
            for d in docs:
                if d["documentName"] == name and name not in seen:
                    selected.append(d)
                    seen.add(name)
                    break

        # 🔥 HARD LIMIT
        selected = selected[:top_k]

        # 🔥 FILL IF MISSING
        if len(selected) < top_k:
            for d in docs:
                if d["documentName"] not in seen:
                    selected.append(d)
                if len(selected) >= top_k:
                    break

                # ====================================================
        # 🔥 PRETTY PRINT SELECTED DOCS
        # ====================================================
        logger.info("📌 ================= SELECTED DOCUMENTS =================")

        for i, d in enumerate(selected, 1):
            logger.info(f"{i}. {d.get('documentName')} ({d.get('uploadDate')})")

        logger.info("📌 =====================================================")

        return selected

    except Exception as e:
        logger.error(f"LLM selection failed: {e}")
        return docs[:top_k]


# =========================================================
# 🔥 FINAL SELECTION
# =========================================================
def pick_best_docs(grouped, logger: Logger):
    all_docs = []

    for docs in grouped.values():
        all_docs.extend(docs)

    if not all_docs:
        return []

    logger.info(f"📄 Total documents found: {len(all_docs)}")

    if len(all_docs) <= 20:
        return llm_select_best_docs(all_docs, logger, top_k=4)

    filtered = keyword_filter_top20(all_docs)
    return llm_select_best_docs(filtered, logger, top_k=4)


# =========================================================
# 🔥 MAIN ENTRY
# =========================================================
def process_verra_project(pid: str, logger: Logger):

    metadata, document_groups = fetch_verra_metadata(pid, logger)

    docs = extract_documents(document_groups)
    grouped = clean_and_group_docs(docs)

    selected = pick_best_docs(grouped, logger)

    return metadata, selected