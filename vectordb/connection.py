from pymilvus import connections
import os
from dotenv import load_dotenv
load_dotenv()

def connect_milvus():
    connections.connect(
        alias="default",
        uri=os.getenv("MILVUS_URI"),
        token=os.getenv("MILVUS_TOKEN")
    )