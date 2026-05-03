import json
import time
from .config import STEP_BACK_ENABLED, DECOMPOSITION_ENABLED
from .step_back.step_back_generator import StepBackGenerator
from .decomposition.recursive_decomposer import RecursiveDecomposer
from .decomposition.subquery_executor import SubqueryExecutor
from .decomposition.aggregation import AnswerAggregator


class QueryTransformationPipeline:
    def __init__(self, retrieval_service, llm_client, policy_service):
        print("⚙️ [PIPELINE INIT] Initializing components...")
        self.step_back = StepBackGenerator(llm_client, policy_service)
        self.decomposer = RecursiveDecomposer(llm_client)
        self.executor = SubqueryExecutor(retrieval_service, llm_client)
        self.aggregator = AnswerAggregator()
        print("✅ [PIPELINE INIT] Ready\n")

    def run(self, query, pid, description: str) -> dict:

        total_start = time.time()
        print("\n🚀 [PIPELINE] START")
        print(f"📌 PID: {pid}")

        # ---------------------------------
        # STEP 1 — STEP-BACK
        # ---------------------------------
        if STEP_BACK_ENABLED:
            print("🔁 [STEP-BACK] Generating step-back query...")
            t = time.time()
            query = self.step_back.generate(description)
            print(f"✅ [STEP-BACK] Done ({round(time.time()-t, 2)}s)")
        else:
            print("⏭️ [STEP-BACK] Skipped")

        # ---------------------------------
        # STEP 2 — DECOMPOSITION
        # ---------------------------------
        if DECOMPOSITION_ENABLED:
            print("🧩 [DECOMPOSE] Breaking into subqueries...")
            t = time.time()
            subqueries = self.decomposer.transform(query, description)
            print(f"✅ [DECOMPOSE] {len(subqueries)} subqueries ({round(time.time()-t, 2)}s)")
        else:
            subqueries = [query]
            print("⏭️ [DECOMPOSE] Skipped (single query)")

        # ---------------------------------
        # STEP 3 — EXECUTION (RETRIEVAL + LLM)
        # ---------------------------------
        print("🔍 [EXECUTE] Running retrieval + LLM for subqueries...")
        t = time.time()

        try:
            context_blocks, evidences = self.executor.execute(subqueries, pid)
            print(f"✅ [EXECUTE] Done ({round(time.time()-t, 2)}s)")
        except Exception as e:
            print(f"❌ [EXECUTE ERROR] {str(e)}")
            return {}

        if not evidences:
            print("⚠️ [EXECUTE] No evidences found → returning empty")
            return {}

        print(f"📄 [EXECUTE] Evidence count: {len(evidences)}")

        # ---------------------------------
        # STEP 4 — AGGREGATION
        # ---------------------------------
        print("🧠 [AGGREGATE] Combining answers...")
        t = time.time()

        try:
            final_answer = self.aggregator.aggregate(query, context_blocks, description)
            print(f"✅ [AGGREGATE] Done ({round(time.time()-t, 2)}s)")
        except Exception as e:
            print(f"❌ [AGGREGATE ERROR] {str(e)}")
            return {}

        # ---------------------------------
        # STEP 5 — PARSING OUTPUT
        # ---------------------------------
        print("📦 [PARSE] Parsing final output...")
        t = time.time()

        try:
            content = final_answer["messages"][-1].content
            content = content.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(content)
        except Exception as e:
            print(f"❌ [PARSE ERROR] {str(e)}")
            return {}

        parsed["evidences"] = evidences

        print(f"✅ [PARSE] Done ({round(time.time()-t, 2)}s)")

        print(f"⏱ [PIPELINE TOTAL] {round(time.time()-total_start, 2)}s")
        print("🎯 [PIPELINE] END\n")

        return parsed