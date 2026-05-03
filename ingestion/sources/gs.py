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
# 🔥 COMMON HEADERS
# =========================================================
def get_headers():
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://registry.goldstandard.org",
        "referer": "https://registry.goldstandard.org/",
        "user-agent": "Mozilla/5.0",
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
            "project_name": data.get("name"),
            "description": data.get("description"),
            "project_status": data.get("status"),
            "country": data.get("country"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "annual_credits": data.get("estimated_annual_credits"),
            "sdgs": data.get("sustainable_development_goals"),
        }

        return metadata, data.get("sustaincert_id")

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

            docs.append({
                "documentName": filename,
                "documentType": req.get("requestType", ""),
                "uploadDate": d.get("uploadedTimestamp"),
                "uri": f"https://assurance-platform.goldstandard.org/api/public/documents/{doc_id}/download"
            })

    return docs


# =========================================================
# 🔥 TEXT NORMALIZATION
# =========================================================
def normalize_text(text: str):
    import re
    from urllib.parse import unquote

    text = unquote(text or "")
    text = text.lower()

    text = re.sub(r"[+_\-]", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


# =========================================================
# 🔥 FUZZY MATCH HELPERS
# =========================================================
def is_annual_report(text):
    import re
    return bool(re.search(r"annu\w*\s+report", text))


def is_monitoring(text):
    import re
    return bool(re.search(r"monitor\w*", text))


def is_perfcert(text):
    import re
    return bool(re.search(r"(performance\s+certification|perfcert|fvr)", text))


def is_verification(text):
    import re
    return bool(re.search(r"verif\w*", text))


def is_pdd(text):
    import re
    return bool(re.search(r"(pdd|project\s+design)", text))


# =========================================================
# 🔥 CLEAN (FIXED)
# =========================================================
def is_noise(doc):
    name = normalize_text(doc.get("documentName") or "")
    return any(k in name for k in ["draft", "summary", "kml", "agreement"])


def clean_docs(docs):
    return [d for d in docs if not is_noise(d)]


# =========================================================
# 🔥 SMART SCORING FILTER
# =========================================================
def keyword_filter_top20(docs):
    from datetime import datetime

    def parse_date(d):
        try:
            return datetime.fromisoformat(d.replace("Z", ""))
        except:
            return datetime.min

    def score(doc):
        text = normalize_text(
            (doc.get("documentName") or "") + " " +
            (doc.get("documentType") or "")
        )

        s = 0

        if is_monitoring(text):
            s += 50

        if is_annual_report(text):
            s += 45

        if is_perfcert(text):
            s += 45

        if is_verification(text):
            s += 30

        if is_pdd(text):
            s += 15

        if "validation" in text:
            s += 5

        if any(k in text for k in ["sdg", "impact", "benefit", "community", "livelihood"]):
            s += 10

        date = parse_date(doc.get("uploadDate", ""))
        s += int(date.timestamp() / 1e9)

        return s

    ranked = sorted(docs, key=score, reverse=True)
    return ranked[:20]


# =========================================================
# 🔥 STRICT LLM SELECTION
# =========================================================
def llm_select_best_docs(docs, logger: Logger, top_k=5):
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
Select EXACTLY {top_k} documents for SDG impact evaluation.

Priority:
1. Monitoring Reports
2. Annual Reports
3. Performance Certification Reports
4. Verification Reports
5. PDD
Avoid validation unless necessary.

Documents:
{doc_list}

Return ONLY JSON array of EXACTLY {top_k} names.
"""

        response = client.invoke(prompt)

        if not response:
            raise ValueError("Empty LLM response")

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
                raise

        selected = []
        seen = set()

        for name in selected_names:
            for d in docs:
                if d["documentName"] == name and name not in seen:
                    selected.append(d)
                    seen.add(name)
                    break

        if len(selected) < top_k:
            for d in docs:
                if d["documentName"] not in seen:
                    selected.append(d)
                    seen.add(d["documentName"])
                if len(selected) == top_k:
                    break

        selected = selected[:top_k]

        return selected

    except Exception as e:
        logger.error(f"❌ LLM failed: {e}")
        return docs[:top_k]


# =========================================================
# 🔥 FINAL SELECTION
# =========================================================
def pick_best_docs(docs, logger: Logger):

    if not docs:
        return []

    logger.info(f"📄 Total docs: {len(docs)}")

    if len(docs) <= 20:
        return llm_select_best_docs(docs, logger, 5)

    filtered = keyword_filter_top20(docs)
    return llm_select_best_docs(filtered, logger, 5)


# =========================================================
# 🔥 MAIN ENTRY
# =========================================================
def process_gs_project(pid: str, logger: Logger, send_update=None):

    safe_update(send_update, pid, "Fetching GS metadata")

    metadata, gsid = fetch_gs_metadata(pid, logger)

    if not gsid:
        return metadata, []

    safe_update(send_update, pid, "Fetching GS documents")

    raw = fetch_gs_documents(gsid, logger)

    safe_update(send_update, pid, "Extracting documents")

    docs = extract_documents(raw)

    safe_update(send_update, pid, f"Found {len(docs)} documents")

    docs = clean_docs(docs)

    safe_update(send_update, pid, "Selecting best documents (AI)")

    selected = pick_best_docs(docs, logger)

    safe_update(send_update, pid, f"Selected {len(selected)} documents")

    return metadata, selected