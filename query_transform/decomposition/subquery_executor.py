from pathlib import Path

class SubqueryExecutor:
    def __init__(self, retrieval_service, llm_client):
        self.retrieval = retrieval_service
        self.llm = llm_client
        self.prompt_template = Path(
            "query_transform/prompts/executor_prompt.txt"
        ).read_text()
        
    def format_qa_pair(self, question: str, answer: str) -> str:
        return f"Question: {question}\nAnswer: {answer}"

    def execute(self, subqueries, pid) -> str:
        q_a_pairs = ""

        for q in subqueries:
            retrieved = self.retrieval.search(
                query=q,
                pid=pid,
                top_k=8
            )

            context = "\n\n".join(
                [
                    f"[Document: {r['document']} | Page: {r['page_number']}]\n{r['content']}"
                    for r in retrieved
                ]
            )

            prompt = self.prompt_template.format(
                q_a_pairs=q_a_pairs,
                q=q,
                context=context
            )

            answer = self.llm.generate(prompt=prompt)

            formatted_pair = self.format_qa_pair(q, answer)

            if q_a_pairs:
                q_a_pairs += "\n---\n" + formatted_pair
            else:
                q_a_pairs = formatted_pair

        return q_a_pairs