import json
import argparse
import os
import time
from pathlib import Path

from llm.utils import SDG_TARGETS_V2
from scripts.utils import setup_logger
from llm.llm_client import GroqLLMClient
from retrieval.retrieval_service import RetrievalService
from query_transform.pipeline import QueryTransformationPipeline

from scoring.modules.rebuild_master import rebuild_master_criteria
from scoring.modules.normalize_projects import normalize as normalize_text

# ---------------------------------
# NORMALIZATION
# ---------------------------------
def normalize_single_project(llm_data, master, sector="forestry"):

    print("🔧 [NORMALIZE] Starting normalization...")

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

    print("✅ [NORMALIZE] Done")
    return {"sdgs": result}


# ---------------------------------
# LLM PIPELINE
# ---------------------------------
def run_pipeline(pid, retrieval_service, retriev_policy_service):

    logger = setup_logger("SDG Prototype + LLM Runner")

    client = GroqLLMClient()
    pipeline = QueryTransformationPipeline(
        retrieval_service=retrieval_service,
        llm_client=client,
        policy_service=retriev_policy_service
    )

    final_output = {}
    total = len(SDG_TARGETS_V2["indicator_mappings"])

    print(f"\n🚀 Running LLM pipeline for {total} indicators...\n")

    for i, target in enumerate(SDG_TARGETS_V2["indicator_mappings"], start=1):

        start_time = time.time()

        sdg_goal = target["SDG"]

        print(f"\n🔥 [{i}/{total}] START → {target['IndicatorId']} ({sdg_goal})")

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
            print("   🔍 Retrieving + LLM processing...")

            final_answer = pipeline.run(description, pid, description)

            print("   ✅ LLM completed")

        except Exception as e:
            print(f"   ❌ ERROR in pipeline: {str(e)}")
            continue

        final_answer["target"] = target["SDG_Target"]
        final_answer["indicator"] = target['Indicator']

        final_output[sdg_goal].append(final_answer)

        print(f"⏱ Done in {round(time.time()-start_time, 2)} sec")

    print("\n🎯 LLM PIPELINE COMPLETE\n")

    return final_output


# ---------------------------------
# MAIN
# ---------------------------------
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--o_p", type=str, required=True)
    parser.add_argument("--projs", type=str, required=True)
    parser.add_argument("--embedding", type=str, default="e5")

    args = parser.parse_args()

    logger = setup_logger("SDG Prototype + LLM Runner")

    print("\n⚙️ Initializing services...\n")

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

    print("✅ Services initialized\n")

    # MASTER BUILD
    print("🔧 Rebuilding master criteria...")
    rebuild_master_criteria(
        input_file_name="sdg_master_criteria.json",
        output_file_name="sector_master_criteria.json"
    )

    master_path = Path("scoring/criteria/sector_master_criteria.json")

    with open(master_path, "r", encoding="utf-8") as f:
        master = json.load(f)

    print("✅ Master loaded\n")

    # PROJECT LOOP
    for proj in os.listdir(args.projs):

        print("\n" + "="*60)
        print(f"🚀 PROJECT: {proj}")
        print("="*60)

        proj_start = time.time()

        # STEP 1 — LLM
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

        print("💾 LLM output saved")

        # STEP 2 — NORMALIZE
        structured = normalize_single_project(results, master)

        structured_file = proj_path / "structured_sdg_results.json"

        with open(structured_file, "w", encoding="utf-8") as f:
            json.dump(structured, f, indent=4)

        print("💾 Structured output saved")

        # STEP 3 — SCORING
        print("📊 Calculating scores...")

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

        print("💾 Final score saved")

        print(f"\n⏱ PROJECT DONE in {round(time.time()-proj_start, 2)} sec")

    print("\n🎯 ALL DONE\n")


if __name__ == "__main__":
    main()