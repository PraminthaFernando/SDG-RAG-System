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
        embed_batch_size = 128
        all_embeddings = []

        with _embedding_lock:
            for i in range(0, len(contents), embed_batch_size):
                batch = contents[i:i + embed_batch_size]
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

        if not policy_docs:
            pids = [doc["pid"] for doc in documents]

        # =========================
        # 🔥 INSERT INTO MILVUS (FIXED)
        # =========================
        insert_batch_size = 200  # 🔥 SAFE (adjust if needed)

        with _store_lock:

            total = len(documents)

            for i in range(0, total, insert_batch_size):

                batch_slice = slice(i, i + insert_batch_size)

                batch_ids = ids[batch_slice]
                batch_docs = documents_names[batch_slice]
                batch_pages = pages[batch_slice]
                batch_chunks = chunks[batch_slice]
                batch_contents = contents[batch_slice]
                batch_embeddings = all_embeddings[batch_slice]

                print(f"🚀 Inserting batch {i} - {i + len(batch_ids)}")

                if policy_docs:
                    self.collection.insert([
                        batch_ids,
                        batch_docs,
                        batch_pages,
                        batch_chunks,
                        batch_contents,
                        batch_embeddings
                    ])
                else:
                    batch_pids = pids[batch_slice]

                    self.collection.insert([
                        batch_ids,
                        batch_docs,
                        batch_pages,
                        batch_chunks,
                        batch_contents,
                        batch_pids,
                        batch_embeddings
                    ])

            # flush once after all inserts
            self.collection.flush()