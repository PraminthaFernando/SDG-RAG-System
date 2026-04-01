from pathlib import Path
from retrieval.retrieval_service import RetrievalService

class StepBackGenerator:
    def __init__(self, llm_client, policy_service : RetrievalService):
        self.llm = llm_client
        self.policy_service = policy_service
        self.prompt_template = Path(
            "query_transform/prompts/step_back_prompt.txt"
        ).read_text()

    def generate(self, query: str) -> str:
        retrieved = self.policy_service.search(
            query=query,
            top_k=10
        )
        policy_context = "\n\n".join(
            [
                f"[Document: {r['document']} | Page: {r['page_number']}]\n{r['content']}"
                for r in retrieved
            ]
        )
        prompt = self.prompt_template.format(
            retrieved_policy_passages=policy_context,
            query=query
        )
        response = self.llm.generate(prompt)
        return response.strip()