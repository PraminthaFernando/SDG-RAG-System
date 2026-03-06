import os

MILVUS_HOST = os.getenv("MILVUS_HOST")
MILVUS_PORT = os.getenv("MILVUS_PORT")

COLLECTIONS = {
    "simCSE": "carbon_related_sentences",
    "e5": "e5_carbon_collection",
    "bge" : "bge_carbon_collection",
    "nomic": "nomic_carbon_collection"
}

METRIC_TYPE = "COSINE"

VECTOR_DIMENSIONS = {
    "simCSE" : 1024,
    "e5" : 1024,
    "bge" : 1024,
    "nomic" : 768
}

INDEX_PARAMS = {
    "index_type": "HNSW",
    "metric_type": METRIC_TYPE,
    "params": {
        "M": 16,
        "efConstruction": 200
    }
}

SEARCH_PARAMS = {
    "metric_type": METRIC_TYPE,
    "params": {"ef": 100}
}