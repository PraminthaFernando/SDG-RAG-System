from pathlib import Path
from typing import Tuple, Dict
from retrieval.retrieval_service import RetrievalService

class SubqueryExecutor:
    def __init__(self, retrieval_service : RetrievalService, llm_client):
        self.retrieval = retrieval_service
        self.llm = llm_client
        self.prompt_template = Path(
            "query_transform/prompts/executor_prompt.txt"
        ).read_text()
        
    def format_qa_pair(self, question: str, answer: str) -> str:
        return f"Question: {question}\nAnswer: {answer}"

    def execute(self, subqueries, pid) -> Tuple[str, Dict]:
        evidences = {}

        for q in subqueries:
            retrieved = self.retrieval.search(
                query=q,
                pid=pid,
                top_k=10
            )
            
            if not retrieved:
                continue
                
            evidences[q] = []
            context_blocks = []
            seen_chunks = set()
            
            for r in retrieved:
                chunk_id = r.get("chunk_number")
                
                if chunk_id in seen_chunks:
                    continue
                seen_chunks.add(chunk_id)
                
                data = {
                    "similarity_score": r["score"],
                    "pid": r["pid"],
                    "document": r["document"],
                    "page_number": r["page_number"],
                    "content": r["content"],
                    "hybrid_score": r["hybrid_score"],
                    "rerank_score": r["rerank_score"]
                }
                evidences[q].append(data)
                context_blocks.append(
                    f"[Document: {r['document']} | Page: {r['page_number']}]\n{r['content']}"
                )

        return (context_blocks, evidences)