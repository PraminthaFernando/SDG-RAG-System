import json
from pathlib import Path
from query_transform.base_transformer import BaseQueryTransformer

class RecursiveDecomposer(BaseQueryTransformer):
    def __init__(self, llm_client):
        self.llm = llm_client
        self.prompt_template = Path(
            "query_transform/prompts/decomposition_prompt.txt"
        ).read_text()

    def transform(self, query: str) -> list[str]:
        prompt = self.prompt_template.format(query=query)
        response = self.llm.generate(prompt)
        try:
            subqueries = json.loads(response)
            return subqueries[:5]
        except Exception:
            return [query]