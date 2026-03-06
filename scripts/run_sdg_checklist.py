import os
import json
import argparse
from pathlib import Path
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import JsonOutputParser

from retrieval.retrieval_service import RetrievalService
from llm.langchain_llm import LangChainGroqLLM
from llm.llm_client import GroqLLMClient
from llm.sdg_prompt_builder import SDGPromptBuilder
from llm.models import SDGEvaluationResult
from scripts.utils import setup_logger

def run_sdg_checklist(data, category, sdg_key, pid=None):

    sdg_checklist = data[category]["sdgs"][sdg_key]

    SDG_label = sdg_checklist["sdg_key"]
    questions = sdg_checklist["questions"]

    retrieval_service = RetrievalService(
        mode="hybrid",
        use_reranker=True,
        collection="simCSE"
    )

    client = GroqLLMClient(temperature=0.0)

    prompt_builder = SDGPromptBuilder()

    parser = JsonOutputParser(pydantic_object=SDGEvaluationResult)

    results = []

    for question in questions:

        question_text = question["question"]

        for query in question["queries"]:

            retrieved = retrieval_service.search(
                query=query,
                pid=pid,
                top_k=10
            )

            context = "\n\n".join(
                [
                    f"[Document: {r['document']} | Page: {r['page_number']}]\n{r['content']}"
                    for r in retrieved
                ]
            )

            prompt = prompt_builder.build(
                sdg_label=SDG_label,
                question=question_text,
                context=context
            )

            response = client.generate_structured(prompt, SDGEvaluationResult)

            # parsed = parser.parse(response_text)

            # parsed = parser.parse(response.content)

            results.append({
                "question_id": question.get("question_id"),
                "query": query,
                "result": response.model_dump()
            })

    return results

def main():
    parser = argparse.ArgumentParser(
        description="Threaded batch ingest for project folder"
    )

    parser.add_argument("--o_p", type=str, required=True)
    parser.add_argument("--i_f", type=str, required=True)
    parser.add_argument("--pid", type=str, required=True)

    args = parser.parse_args()
    logger = setup_logger("SDG Checklist Runner")
    
    with open(args.i_f, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    logger.info(f"Loaded checklist")

    results = run_sdg_checklist(
        data=data,
        category="Forestry",
        sdg_key="SDG_15_Life_On_Land",
        pid=args.pid
    )
    
    output_path = Path(args.o_p)

    if not output_path.exists():
        logger.info(f"Creating output directory: {output_path}")
        output_path.mkdir(parents=True, exist_ok=True)

    output_file = output_path / "sdg_results.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    logger.info(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()