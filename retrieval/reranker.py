import torch
from sentence_transformers import CrossEncoder
from typing import List

class CrossEncoderReranker:

    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = CrossEncoder(model_name, device=str(self.device))

    def rerank(self, query: str, results: List[dict], top_k: int = 5) -> List[dict]:

        pairs = [(query, r["content"]) for r in results]
        scores = self.model.predict(pairs)

        for r, score in zip(results, scores):
            r["rerank_score"] = float(score)

        sorted_results = sorted(
            results,
            key=lambda x: x["rerank_score"],
            reverse=True
        )

        return sorted_results[:top_k]