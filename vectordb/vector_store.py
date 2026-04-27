from typing import List
from pymilvus import Collection
from .collection_manager import CollectionManager
import threading

_store_lock = threading.Lock()
_embedding_lock = threading.Lock()


class VectorStore:

    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.collection_manager = CollectionManager()
        self.collection = None

    def initialize(self, reset=False, model: str = "e5", collection: str = "e5"):
        self.collection = self.collection_manager.create_collection(
            reset=reset,
            model=model,
            collection=collection
        )

    def insert_documents(self, documents: List[dict], policy_docs: bool = False):

        """
        documents format:
        [
            {
                "id": str,
                "pid": str,
                "document": str,
                "page_number": int,
                "chunk_number": int,
                "content": str
            }
        ]
        """

        # =========================
        # 🔥 PREPARE CONTENTS
        # =========================
        contents = [doc["content"] for doc in documents]

        # =========================
        # 🔥 BATCHED EMBEDDING
        # =========================
        batch_size = 128
        all_embeddings = []

        with _embedding_lock:
            for i in range(0, len(contents), batch_size):
                batch = contents[i:i + batch_size]
                print(f"🔄 Embedding batch {i} - {i + len(batch)} / {len(contents)}")

                batch_embeddings = self.embedding_model.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)

        # =========================
        # 🔥 PREPARE METADATA
        # =========================
        documents_names = [doc["document"] for doc in documents]
        pages = [doc["page_number"] for doc in documents]
        chunks = [doc["chunk_number"] for doc in documents]
        ids = [doc["id"] for doc in documents]

        # =========================
        # 🔥 INSERT INTO MILVUS
        # =========================
        with _store_lock:

            if policy_docs:
                self.collection.insert([
                    ids,
                    documents_names,
                    pages,
                    chunks,
                    contents,
                    all_embeddings
                ])

            else:
                pids = [doc["pid"] for doc in documents]

                self.collection.insert([
                    ids,
                    documents_names,
                    pages,
                    chunks,
                    contents,
                    pids,
                    all_embeddings
                ])

            self.collection.flush()