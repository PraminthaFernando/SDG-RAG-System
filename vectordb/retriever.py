from typing import List
from .config import SEARCH_PARAMS

class Retriever:

    def __init__(self, collection, embedding_model):
        self.collection = collection
        self.embedding_model = embedding_model

    def search(self, query: str, pid: str = None, top_k: int = 5):

        query_vector = self.embedding_model.embed_query(query)

        expr = None
        if pid is not None:
            expr = f"pid == {str(pid)}"

        results = self.collection.search(
            data=[query_vector],
            anns_field="vector",
            param=SEARCH_PARAMS,
            limit=top_k,
            expr=expr,
            output_fields=[
                "pid",
                "document",
                "page_number",
                "chunk_number",
                "content"
            ]
        )

        formatted_results = []

        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "score": hit.score,
                    "pid": hit.entity.get("pid"),
                    "document": hit.entity.get("document"),
                    "page_number": hit.entity.get("page_number"),
                    "chunk_number": hit.entity.get("chunk_number"),
                    "content": hit.entity.get("content")
                })

        return formatted_results