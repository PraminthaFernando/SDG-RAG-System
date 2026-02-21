from pymilvus import connections
from .config import MILVUS_HOST, MILVUS_PORT

def connect_milvus():
    connections.connect(
        alias="default",
        host=MILVUS_HOST,
        port=MILVUS_PORT
    )