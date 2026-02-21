from embeddings.embedding_factory import EmbeddingFactory
from vectordb.collection_manager import CollectionManager
from vectordb.retriever import Retriever
from .base_pipeline import BasePipeline
from .utils import setup_pipeline_logger

class RetrievalPipeline(BasePipeline):

    def __init__(self, query: str, pid: int = None, top_k: int = 5):
        self.query = query
        self.pid = pid
        self.top_k = top_k
        self.logger = setup_pipeline_logger("RetrievalPipeline")

    def run(self):

        self.logger.info("Starting retrieval")

        embedding_model = EmbeddingFactory.create("e5")
        manager = CollectionManager()
        collection = manager.get_collection()

        retriever = Retriever(collection, embedding_model)

        results = retriever.search(
            query=self.query,
            pid=self.pid,
            top_k=self.top_k
        )

        self.logger.info(f"Retrieved {len(results)} results.")

        return results