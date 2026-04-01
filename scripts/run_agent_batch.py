import json
import argparse
import os
from pathlib import Path

from llm.utils import SDG_TARGETS_V2
from scripts.utils import setup_logger
from llm.llm_client import GroqLLMClient
from retrieval.retrieval_service import RetrievalService
from query_transform.pipeline import QueryTransformationPipeline

def run_pipeline(pid, retrieval_service : RetrievalService, retriev_policy_service : RetrievalService):

    logger = setup_logger("SDG Prototype + LLM Runner")
    
    client = GroqLLMClient()
    pipeline = QueryTransformationPipeline(
        retrieval_service=retrieval_service, 
        llm_client=client, 
        policy_service=retriev_policy_service
    )

    final_output = {}

    for target in SDG_TARGETS_V2["indicator_mappings"]:
        sdg_goal = target["SDG"]

        logger.info("=" * 60)
        logger.info(f"Evaluating {sdg_goal}")

        if sdg_goal not in final_output:
            final_output[sdg_goal] = []

        logger.info(f"Target {target['IndicatorId']}")

        description = f"""
SDG goal: {sdg_goal}

SDG target: {target['SDG_Target']}

SDG indicator: {target['Indicator']}

Description: {target['Description']}

Guidance, calculation method and other considerations: {target['Guidance, calculation method and other considerations']}

Data Unit: {target['Data Unit']}
    """

        logger.info(f"Running pipeline for: {target['IndicatorId']}")

        final_answer = pipeline.run(description, pid, description)
        final_answer["target"] = target["SDG_Target"]
        final_answer["indicator"] = target['Indicator']

        logger.info("=" * 60)

        final_output[sdg_goal].append(final_answer)

    return final_output

def main():

    parser = argparse.ArgumentParser(
        description="Prototype + LLM SDG Evaluation"
    )

    parser.add_argument("--o_p", type=str, required=True)
    parser.add_argument("--projs", type=str, required=True)
    parser.add_argument("--embedding", type=str, default="e5")

    args = parser.parse_args()

    logger = setup_logger("SDG Prototype + LLM Runner")
    
    retrieval_service = RetrievalService(
        mode="hybrid",
        use_reranker=True,
        model=args.embedding,
        collection="bge"   # ✅ FIXED
    )
    retriev_policy_service = RetrievalService(
        mode="hybrid",
        use_reranker=True,
        model=args.embedding,
        collection="policy_docs"
    )
       
    for proj in os.listdir(args.projs): 
        logger.info(f"Analyzing {proj}...")
        results = run_pipeline(
            pid=proj,
            retrieval_service=retrieval_service,
            retriev_policy_service=retriev_policy_service
        )

        output_path = Path(args.o_p)
        output_proj_path = output_path / proj
        output_proj_path.mkdir(parents=True, exist_ok=True)

        output_file = output_proj_path / f"{args.embedding}_sdg_prototype_llm_results.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        logger.info("=" * 60)
        logger.info(f"Results saved to {output_file}")
        logger.info("=" * 60)

if __name__ == "__main__":
    main()