from typing import List
from vectordb.retriever import Retriever as MilvusRetriever
from vectordb.collection_manager import CollectionManager
from embeddings.embedding_factory import EmbeddingFactory
from .base_retriever import BaseRetriever


class DenseRetriever(BaseRetriever):

    def __init__(self):
        self.embedding_model = EmbeddingFactory.create("e5")
        manager = CollectionManager()
        self.collection = manager.get_collection()
        self.retriever = MilvusRetriever(self.collection, self.embedding_model)

    def retrieve(self, query: str, pid: int = None, top_k: int = 5) -> List[dict]:

        return self.retriever.search(
            query=query,
            pid=pid,
            top_k=top_k
        )