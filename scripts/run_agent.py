import json
import argparse
import time
import asyncio
from pathlib import Path

from llm.utils import SDG_TARGETS_V2
from scripts.utils import setup_logger
from llm.llm_client import GroqLLMClient
from retrieval.retrieval_service import RetrievalService
from query_transform.pipeline import QueryTransformationPipeline

from scoring.modules.rebuild_master import rebuild_master_criteria
from scoring.modules.normalize_projects import normalize as normalize_text


# ---------------------------------
# NORMALIZATION (UNCHANGED)
# ---------------------------------
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


# ---------------------------------
# LLM PIPELINE WITH PROGRESS
# ---------------------------------
def run_pipeline(pid, retrieval_service, retriev_policy_service, progress_callback=None):

    client = GroqLLMClient()
    pipeline = QueryTransformationPipeline(
        retrieval_service=retrieval_service,
        llm_client=client,
        policy_service=retriev_policy_service
    )

    final_output = {}
    total = len(SDG_TARGETS_V2["indicator_mappings"])

    for i, target in enumerate(SDG_TARGETS_V2["indicator_mappings"], start=1):

        # 🔥 SEND PROGRESS
        if progress_callback:
            progress_callback(i, total, target["Indicator"])

        sdg_goal = target["SDG"]

        if sdg_goal not in final_output:
            final_output[sdg_goal] = []

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
        except:
            continue

        final_answer["target"] = target["SDG_Target"]
        final_answer["indicator"] = target['Indicator']

        final_output[sdg_goal].append(final_answer)

    return final_output


# ---------------------------------
# 🔥 ASYNC PIPELINE WITH CLEAN TRACKING
# ---------------------------------
async def run_agent_with_progress(project_id, output_path, embedding, send_update):

    logger = setup_logger("SDG Agent")

    # 🔥 CLEAN START
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

    # MASTER (no noisy logs)
    rebuild_master_criteria(
        input_file_name="sdg_master_criteria.json",
        output_file_name="sector_master_criteria.json"
    )

    master_path = Path("scoring/criteria/sector_master_criteria.json")

    with open(master_path, "r", encoding="utf-8") as f:
        master = json.load(f)

    await send_update(project_id, "Running SDG analysis")

    loop = asyncio.get_event_loop()

    # 🔥 PROGRESS CALLBACK
    def progress_callback(i, total, indicator_name):
        msg = f"Evaluating {i}/{total}: {indicator_name[:60]}"
        asyncio.run_coroutine_threadsafe(
            send_update(project_id, msg),
            loop
        )

    # RUN LLM
    results = await loop.run_in_executor(
        None,
        lambda: run_pipeline(
            pid=project_id,
            retrieval_service=retrieval_service,
            retriev_policy_service=retriev_policy_service,
            progress_callback=progress_callback
        )
    )

    proj_path = Path(output_path) / project_id
    proj_path.mkdir(parents=True, exist_ok=True)

    llm_file = proj_path / f"{embedding}_sdg_prototype_llm_results.json"

    with open(llm_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    await send_update(project_id, "LLM processing completed")

    # NORMALIZE
    await send_update(project_id, "Normalizing results")

    structured = normalize_single_project(results, master)

    structured_file = proj_path / "structured_sdg_results.json"

    with open(structured_file, "w", encoding="utf-8") as f:
        json.dump(structured, f, indent=4)

    # SCORING
    await send_update(project_id, "Calculating final score")

    project_data = structured
    sector = "forestry"
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

            target_score = score_sum / (2 * total)
            target_scores.append(target_score)

        sdg_score = sum(target_scores) / len(target_scores) if target_scores else 0

        output_sdgs[sdg_id] = {"score": sdg_score}
        sdg_scores.append(sdg_score)

    final_score = sum(sdg_scores) / len(sdg_scores) if sdg_scores else 0

    final_output = {
        "sector": "forestry",
        "final_score": final_score,
        "sdgs": output_sdgs
    }

    final_file = proj_path / "project_impact_score.json"

    with open(final_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4)

    await send_update(project_id, "Final score saved")

    await send_update(project_id, "SDG analysis completed", "done")


# ---------------------------------
# CLI (UNCHANGED)
# ---------------------------------
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--o_p", type=str, required=True)
    parser.add_argument("--project", type=str, required=True)
    parser.add_argument("--embedding", type=str, default="e5")

    args = parser.parse_args()

    retrieval_service = RetrievalService(
        mode="hybrid",
        use_reranker=True,
        model=args.embedding,
        collection="nomic"
    )

    retriev_policy_service = RetrievalService(
        mode="hybrid",
        use_reranker=True,
        model=args.embedding,
        collection="policy_docs"
    )

    rebuild_master_criteria(
        input_file_name="sdg_master_criteria.json",
        output_file_name="sector_master_criteria.json"
    )

    master_path = Path("scoring/criteria/sector_master_criteria.json")

    with open(master_path, "r", encoding="utf-8") as f:
        master = json.load(f)

    proj = args.project

    results = run_pipeline(
        pid=proj,
        retrieval_service=retrieval_service,
        retriev_policy_service=retriev_policy_service
    )

    proj_path = Path(args.o_p) / proj
    proj_path.mkdir(parents=True, exist_ok=True)

    llm_file = proj_path / f"{args.embedding}_sdg_prototype_llm_results.json"

    with open(llm_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)


if __name__ == "__main__":
    main()