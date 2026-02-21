import argparse
from pymilvus import Collection
from vectordb.collection_manager import CollectionManager
from scripts.ingest_project import main as ingest_main

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--file", type=str, required=True)
    args = parser.parse_args()

    manager = CollectionManager()
    collection = manager.get_collection()

    expr = f"pid == {args.pid}"
    collection.delete(expr)

    print(f"Deleted old vectors for pid {args.pid}")

    ingest_main()


if __name__ == "__main__":
    main()