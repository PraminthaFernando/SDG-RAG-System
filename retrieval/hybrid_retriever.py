from typing import List
from collections import Counter
from .dense_retriever import DenseRetriever
from .base_retriever import BaseRetriever

class HybridRetriever(BaseRetriever):

    def __init__(self, keyword_weight: float = 0.2):
        self.dense = DenseRetriever()
        self.keyword_weight = keyword_weight

    def _keyword_score(self, query: str, text: str) -> float:
        query_terms = query.lower().split()
        text_terms = text.lower().split()

        counter = Counter(text_terms)
        score = sum(counter.get(term, 0) for term in query_terms)

        return float(score)

    def retrieve(self, query: str, pid: int = None, top_k: int = 5) -> List[dict]:

        dense_results = self.dense.retrieve(query, pid, top_k * 2)

        for result in dense_results:
            keyword_score = self._keyword_score(query, result["content"])
            result["hybrid_score"] = (
                result["score"] +
                self.keyword_weight * keyword_score
            )

        sorted_results = sorted(
            dense_results,
            key=lambda x: x["hybrid_score"],
            reverse=True
        )

        return sorted_results[:top_k]