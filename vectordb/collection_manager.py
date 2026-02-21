from pymilvus import Collection, utility
from .config import COLLECTION_NAME, INDEX_PARAMS
from .schema import create_schema
from .connection import connect_milvus


class CollectionManager:

    def __init__(self):
        connect_milvus()

    def create_collection(self, reset=False):

        if utility.has_collection(COLLECTION_NAME):
            if reset:
                utility.drop_collection(COLLECTION_NAME)
            else:
                return Collection(COLLECTION_NAME)

        schema = create_schema()
        collection = Collection(
            name=COLLECTION_NAME,
            schema=schema
        )

        collection.create_index(
            field_name="vector",
            index_params=INDEX_PARAMS
        )

        collection.load()

        return collection

    def get_collection(self):
        return Collection(COLLECTION_NAME)