import json
from .config import STEP_BACK_ENABLED, DECOMPOSITION_ENABLED
from .step_back.step_back_generator import StepBackGenerator
from .decomposition.recursive_decomposer import RecursiveDecomposer
from .decomposition.subquery_executor import SubqueryExecutor
from .decomposition.aggregation import AnswerAggregator

class QueryTransformationPipeline:
    def __init__(self, retrieval_service, llm_client):
        self.step_back = StepBackGenerator(llm_client)
        self.decomposer = RecursiveDecomposer(llm_client)
        self.executor = SubqueryExecutor(retrieval_service, llm_client)
        self.aggregator = AnswerAggregator()

    def run(self, query, pid, description : str) -> dict:

        # Step-back
        if STEP_BACK_ENABLED:
            query = self.step_back.generate(description)

        # Decomposition
        if DECOMPOSITION_ENABLED:
            subqueries = self.decomposer.transform(query)
        else:
            subqueries = [query]

        sub_answers = self.executor.execute(subqueries, pid)
        final_answer = self.aggregator.aggregate(query, sub_answers, description)
        content = final_answer["messages"][-1].content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)