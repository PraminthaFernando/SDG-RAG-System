from vectordb.vector_store import VectorStore
from embeddings.embedding_factory import EmbeddingFactory
from scripts.utils import setup_logger


def main():
    logger = setup_logger()

    logger.info("Rebuilding Milvus collection...")

    embedding_model = EmbeddingFactory.create("e5")

    vector_store = VectorStore(embedding_model)
    vector_store.initialize(reset=True)

    logger.info("Collection rebuilt successfully.")


if __name__ == "__main__":
    main()