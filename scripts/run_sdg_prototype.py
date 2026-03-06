import json
import argparse
from pathlib import Path

from llm.models import SDGEvaluationResult
from llm.llm_client import GroqLLMClient
from llm.prompt_builder_factory import PromptBuilderFactory
from scripts.utils import setup_logger, SDG_PROTOTYPES
from retrieval.retrieval_service import RetrievalService

def evaluate_target(client : GroqLLMClient, sdg_key : str, target_code : str, evidence_list):

    if not evidence_list:
        return {
            "score": 0,
            "summary": "No relevant evidence found."
        }

    combined_text = "\n\n".join(
        [
            f"[Document: {r['document']} | Page: {r['page_number']}]\n{r['sentence']}"
            for r in evidence_list
        ]
    )

    prompt_builder = PromptBuilderFactory.create("prototype")
    system_prompt = prompt_builder.build(sdg_key=sdg_key, target_code=target_code, evidence=combined_text)

    response = client.generate_structured(
        prompt=system_prompt,
        schema=SDGEvaluationResult
    )

    return {
        "code": target_code,
        "result": response.model_dump()
    }

def run_pipeline(pid, embedding_model="simCSE"):

    logger = setup_logger("SDG Prototype + LLM Runner")

    retrieval_service = RetrievalService(
        mode="hybrid",
        use_reranker=True,
        collection=embedding_model
    )

    client = GroqLLMClient()

    final_output = {}

    for sdg_key, targets in SDG_PROTOTYPES.items():

        logger.info("=" * 60)
        logger.info(f"Evaluating {sdg_key}")

        final_output[sdg_key] = {}

        for target_code, prototypes in targets.items():

            logger.info(f"Target {target_code}")

            all_results = []

            for proto in prototypes:
                results = retrieval_service.search(
                    query=proto,
                    pid=pid,
                    top_k=8
                )
                all_results.extend(results)

            # Deduplicate by sentence
            unique = {}
            for r in all_results:
                unique[r["content"]] = r

            retrieved = list(unique.values())

            evidence_list = []

            for r in retrieved:
                evidence_entry = {
                    "sentence": r["content"],
                    "document": r.get("document"),
                    "page_number": r.get("page_number")
                }
                evidence_list.append(evidence_entry)

            logger.info(f"Evidence count: {len(evidence_list)}")

            llm_result = evaluate_target(
                sdg_key=sdg_key,
                client=client,
                target_code=target_code,
                evidence_list=evidence_list
            )

            final_output[sdg_key][target_code] = llm_result

    return final_output

def main():

    parser = argparse.ArgumentParser(
        description="Prototype + LLM SDG Evaluation"
    )

    parser.add_argument("--o_p", type=str, required=True)
    parser.add_argument("--pid", type=str, required=True)
    parser.add_argument("--embedding", type=str, default="e5")

    args = parser.parse_args()

    logger = setup_logger("SDG Prototype + LLM Runner")

    results = run_pipeline(
        pid=args.pid,
        embedding_model=args.embedding
    )

    output_path = Path(args.o_p)
    output_path.mkdir(parents=True, exist_ok=True)

    output_file = output_path / f"{args.embedding}_sdg_prototype_llm_results.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    logger.info("=" * 60)
    logger.info(f"Results saved to {output_file}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()