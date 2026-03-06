from pymilvus import Collection, utility
from .config import INDEX_PARAMS, COLLECTIONS
from .schema import create_schema
from .connection import connect_milvus

class CollectionManager:

    def __init__(self):
        connect_milvus()

    def create_collection(self, reset=False, collection: str = "e5"):
        collection_name = COLLECTIONS[collection]
        if utility.has_collection(collection_name):
            if reset:
                utility.drop_collection(collection_name)
            else:
                return Collection(collection_name)

        schema = create_schema(collection=collection)
        collection = Collection(
            name=collection_name,
            schema=schema
        )

        collection.create_index(
            field_name="vector",
            index_params=INDEX_PARAMS
        )

        collection.load()

        return collection

    def get_collection(self, collection : str = "e5"):
        return Collection(COLLECTIONS[collection])