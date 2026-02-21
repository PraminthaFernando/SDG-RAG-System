MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"

COLLECTION_NAME = "e5_carbon_collection"

VECTOR_DIMENSION = 1024  # E5-large
METRIC_TYPE = "COSINE"

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