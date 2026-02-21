from typing import List
from .dense_retriever import DenseRetriever
from .hybrid_retriever import HybridRetriever
from .reranker import CrossEncoderReranker

class RetrievalService:

    def __init__(
        self,
        mode: str = "dense",
        use_reranker: bool = False
    ):

        if mode == "dense":
            self.retriever = DenseRetriever()
        elif mode == "hybrid":
            self.retriever = HybridRetriever()
        else:
            raise ValueError("Invalid retrieval mode")

        self.use_reranker = use_reranker
        self.reranker = CrossEncoderReranker() if use_reranker else None

    def search(
        self,
        query: str,
        pid: int = None,
        top_k: int = 5
    ) -> List[dict]:

        results = self.retriever.retrieve(
            query=query,
            pid=pid,
            top_k=top_k * 2 if self.use_reranker else top_k
        )

        if self.use_reranker:
            results = self.reranker.rerank(
                query=query,
                results=results,
                top_k=top_k
            )

        return results