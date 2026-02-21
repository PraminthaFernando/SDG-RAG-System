from typing import List
from pymilvus import Collection
from .collection_manager import CollectionManager
from .config import COLLECTION_NAME
import threading

_store_lock = threading.Lock()
_embedding_lock = threading.Lock()

class VectorStore:

    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.collection_manager = CollectionManager()
        self.collection = None

    def initialize(self, reset=False):
        self.collection = self.collection_manager.create_collection(reset=reset)

    def insert_documents(self, documents: List[dict]):

        """
        documents format:
        [
            {
                "id": str,
                "pid": int,
                "document": str,
                "page_number": int,
                "chunk_number": int,
                "content": str
            }
        ]
        """
        contents = [doc["content"] for doc in documents]
        with _embedding_lock:
            embeddings = self.embedding_model.embed_documents(contents)

        ids = [doc["id"] for doc in documents]
        pids = [doc["pid"] for doc in documents]
        documents_names = [doc["document"] for doc in documents]
        pages = [doc["page_number"] for doc in documents]
        chunks = [doc["chunk_number"] for doc in documents]

        with _store_lock:
            self.collection.insert([
                ids,
                pids,
                documents_names,
                pages,
                chunks,
                contents,
                embeddings
            ])

            self.collection.flush()