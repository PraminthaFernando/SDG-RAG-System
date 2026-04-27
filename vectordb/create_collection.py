from pymilvus import (
    connections,
    FieldSchema, CollectionSchema, DataType,
    Collection, utility
)
import os
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME = "nomic"

def connect():
    connections.connect(
        alias="default",
        uri=os.getenv("MILVUS_URI"),
        token=os.getenv("MILVUS_TOKEN")
    )

def drop_if_exists():
    if utility.has_collection(COLLECTION_NAME):
        print("⚠️ Collection already exists. Dropping...")
        utility.drop_collection(COLLECTION_NAME)
        print("🗑️ Old collection dropped")

def create_collection():
    fields = [
        # PRIMARY KEY
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=512),

        # MUST MATCH policy_docs insert (NO pid)
        FieldSchema(name="document", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="page_number", dtype=DataType.INT64),
        FieldSchema(name="chunk_number", dtype=DataType.INT64),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),

        # VECTOR FIELD LAST
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=768)
    ]

    schema = CollectionSchema(fields, description="Policy document embeddings")

    collection = Collection(name=COLLECTION_NAME, schema=schema)

    print("📦 Creating index...")

    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "COSINE",
        "params": {"nlist": 128}
    }

    collection.create_index(field_name="vector", index_params=index_params)

    print("📥 Loading collection...")
    collection.load()

    print("✅ Collection created and loaded successfully!")

if __name__ == "__main__":
    print("🔌 Connecting to Zilliz...")
    connect()

    drop_if_exists()
    create_collection()