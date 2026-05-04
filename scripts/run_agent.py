
import json
import argparse
import asyncio
from pathlib import Path

from llm.utils import SDG_TARGETS_V2
from scripts.utils import setup_logger
from llm.llm_client import GroqLLMClient
from retrieval.retrieval_service import RetrievalService
from query_transform.pipeline import QueryTransformationPipeline

from scoring.modules.rebuild_master import rebuild_master_criteria
from scoring.modules.normalize_projects import normalize as normalize_text

from RDS.fetch_type import get_project_sector

# 🔥 NEW IMPORTS
from sqlalchemy.exc import OperationalError
from sqlalchemy import text


# =========================================================
# NORMALIZATION
# =========================================================
def normalize_single_project(llm_data, master, sector="forestry"):

    result = {}

    for sdg_text, entries in llm_data.items():

        try:
            sdg_id, sdg_name = sdg_text.split(".", 1)
        except:
            continue

        result.setdefault(sdg_id, {
            "sdg_id": sdg_id,
            "sdg_name": sdg_name.strip(),
            "targets": {}
        })

        for e in entries:

            target_text = e.get("target", "")
            indicator_text = e.get("indicator", "")
            score = e.get("score", 0)

            if not target_text or not indicator_text:
                continue

            target_id = target_text.split(" ")[0]
            matched_id = None

            for s, s_data in master["sectors"].items():
                if s != sector:
                    continue

                for sdg_k, sdg_data in s_data["sdgs"].items():
                    if sdg_k != sdg_id:
                        continue

                    for t_k, t_data in sdg_data["targets"].items():
                        if t_k != target_id:
                            continue

                        for ind_id, ind in t_data["indicators"].items():
                            if normalize_text(indicator_text) == normalize_text(ind["indicator_text"]):
                                matched_id = ind_id
                                break

            if not matched_id:
                continue

            target_obj = result[sdg_id]["targets"].setdefault(target_id, {
                "target_id": target_id,
                "target_text": target_text,
                "indicators": {}
            })

            target_obj["indicators"][matched_id] = {
                "indicator_id": matched_id,
                "score": score
            }

    return {"sdgs": result}


# =========================================================
# LLM PIPELINE
# =========================================================
def run_pipeline(pid, retrieval_service, retriev_policy_service, sector, progress_callback=None):

    client = GroqLLMClient()

    pipeline = QueryTransformationPipeline(
        retrieval_service=retrieval_service,
        llm_client=client,
        policy_service=retriev_policy_service
    )

    mappings = SDG_TARGETS_V2["sectors"][sector]["indicator_mappings"]

    final_output = {}
    total = len(mappings)

    for i, target in enumerate(mappings, start=1):

        if progress_callback:
            progress_callback(i, total, target["Indicator"])

        sdg_goal = target["SDG"]
        final_output.setdefault(sdg_goal, [])

        description = f"""
SDG goal: {sdg_goal}
SDG target: {target['SDG_Target']}
SDG indicator: {target['Indicator']}
Description: {target['Description']}
Guidance: {target['Guidance, calculation method and other considerations']}
Data Unit: {target['Data Unit']}
"""

        try:
            final_answer = pipeline.run(description, pid, description)
        except Exception as e:
            print(f"[{pid}] ❌ LLM failed: {e}")
            continue

        final_answer["target"] = target["SDG_Target"]
        final_answer["indicator"] = target['Indicator']

        final_output[sdg_goal].append(final_answer)

    return final_output


# =========================================================
# MAIN PIPELINE
# =========================================================
async def run_agent_with_progress(project_id, embedding, send_update):

    logger = setup_logger("SDG Agent")

    await send_update(project_id, "Starting SDG analysis")

    retrieval_service = RetrievalService(
        mode="hybrid",
        use_reranker=True,
        model=embedding,
        collection="nomic"
    )

    retriev_policy_service = RetrievalService(
        mode="hybrid",
        use_reranker=True,
        model=embedding,
        collection="policy_docs"
    )

    from RDS.database import SessionLocal

    db = SessionLocal()
    try:
        sector_info = get_project_sector(db, project_id)
        sector = sector_info.get("sector", "renewables")
    finally:
        db.close()

    await send_update(project_id, f"Detected sector: {sector}")

    rebuild_master_criteria(
        input_file_name="sdg_master_criteria.json",
        output_file_name="sector_master_criteria.json"
    )

    master_path = Path("scoring/criteria/sector_master_criteria.json")

    with open(master_path, "r", encoding="utf-8") as f:
        master = json.load(f)

    await send_update(project_id, "Running SDG analysis")

    loop = asyncio.get_event_loop()

    def progress_callback(i, total, indicator_name):
        msg = f"Evaluating {i}/{total}: {indicator_name[:60]}"
        asyncio.run_coroutine_threadsafe(
            send_update(project_id, msg),
            loop
        )

    # ================= LLM =================
    try:
        results = await loop.run_in_executor(
            None,
            lambda: run_pipeline(
                pid=project_id,
                retrieval_service=retrieval_service,
                retriev_policy_service=retriev_policy_service,
                sector=sector,
                progress_callback=progress_callback
            )
        )
    except Exception as e:
        await send_update(project_id, f"❌ LLM execution failed: {str(e)}", "failed")
        return

    if not results:
        raise RuntimeError(f"[{project_id}] ❌ No LLM results generated")

    # ================= SAVE LLM =================
    await send_update(project_id, "Saving LLM results (S3 upload)")

    from RDS.crud_llm import upsert_llm_result

    success = False

    for attempt in range(3):
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            upsert_llm_result(db, project_id, results)
            db.commit()
            success = True
            break

        except OperationalError as e:
            print(f"[{project_id}] ⚠️ retry {attempt+1}: {e}")
            db.rollback()

        except Exception as e:
            print(f"[{project_id}] ❌ DB write failed: {e}")
            db.rollback()
            break

        finally:
            db.close()

    if not success:
        raise RuntimeError(f"[{project_id}] ❌ CRITICAL: Failed to store LLM results")

    await send_update(project_id, "LLM processing completed")

    # ================= NORMALIZE =================
    structured = normalize_single_project(results, master, sector=sector)
    del results

    # ================= SCORING =================
    await send_update(project_id, "Calculating final score")

    project_data = structured
    master_sdgs = master["sectors"][sector]["sdgs"]

    sdg_scores = []
    output_sdgs = {}

    for sdg_id, sdg_data in master_sdgs.items():

        target_scores = []

        for target_id, target_data in sdg_data["targets"].items():

            indicators = target_data["indicators"]
            total = len(indicators)

            if total == 0:
                continue

            score_sum = 0

            for ind_id in indicators.keys():
                val = (
                    project_data.get("sdgs", {})
                    .get(sdg_id, {})
                    .get("targets", {})
                    .get(target_id, {})
                    .get("indicators", {})
                    .get(ind_id, {})
                    .get("score", 0)
                )

                score_sum += min(val, 2)

            target_scores.append(score_sum / (2 * total))

        sdg_score = sum(target_scores) / len(target_scores) if target_scores else 0

        output_sdgs[sdg_id] = {"score": sdg_score}
        sdg_scores.append(sdg_score)

    final_output = {
        "sector": sector,
        "final_score": sum(sdg_scores) / len(sdg_scores) if sdg_scores else 0,
        "sdgs": output_sdgs
    }

    # ================= SAVE SCORE =================
    await send_update(project_id, "Saving score to database")

    from RDS.crud_score import upsert_full_score

    success = False

    for attempt in range(3):
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            upsert_full_score(db, project_id, final_output)
            db.commit()
            success = True
            break

        except OperationalError as e:
            print(f"[{project_id}] ⚠️ retry {attempt+1}: {e}")
            db.rollback()

        except Exception as e:
            print(f"[{project_id}] ❌ Score write failed: {e}")
            db.rollback()
            break

        finally:
            db.close()

    if not success:
        raise RuntimeError(f"[{project_id}] ❌ CRITICAL: Failed to store score")

    await send_update(project_id, "Final score saved")
    await send_update(project_id, "SDG analysis completed", "done")


# =========================================================
# CLI
# =========================================================
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=str, required=True)
    parser.add_argument("--embedding", type=str, default="e5")

    args = parser.parse_args()

    async def console_update(pid, msg, status="running"):
        print(f"[{pid}] {msg}")

    asyncio.run(
        run_agent_with_progress(
            project_id=args.project,
            embedding=args.embedding,
            send_update=console_update
        )
    )


if __name__ == "__main__":
    main()