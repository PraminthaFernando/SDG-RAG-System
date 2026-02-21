import argparse
from embeddings.embedding_factory import EmbeddingFactory
from vectordb.collection_manager import CollectionManager
from vectordb.retriever import Retriever
from scripts.utils import setup_logger

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, required=True)
    parser.add_argument("--pid", type=int, required=False)
    parser.add_argument("--top_k", type=int, default=5)

    args = parser.parse_args()
    logger = setup_logger()

    embedding_model = EmbeddingFactory.create("e5")
    manager = CollectionManager()
    collection = manager.get_collection()

    retriever = Retriever(collection, embedding_model)

    results = retriever.search(
        query=args.query,
        pid=args.pid,
        top_k=args.top_k
    )

    for r in results:
        print("=" * 50)
        print(f"Score: {r['score']}")
        print(f"PID: {r['pid']}")
        print(f"Page: {r['page_number']}")
        print(r["content"][:300])


if __name__ == "__main__":
    main()