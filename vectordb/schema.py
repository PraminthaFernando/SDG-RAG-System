from pymilvus import (
    FieldSchema,
    CollectionSchema,
    DataType
)
from .config import VECTOR_DIMENSION


def create_schema():

    fields = [
        FieldSchema(
            name="id",
            dtype=DataType.VARCHAR,
            is_primary=True,
            auto_id=False,
            max_length=200
        ),
        FieldSchema(
            name="pid",
            dtype=DataType.VARCHAR,
            max_length=20
        ),
        FieldSchema(
            name="document",
            dtype=DataType.VARCHAR,
            max_length=255
        ),
        FieldSchema(
            name="page_number",
            dtype=DataType.INT64
        ),
        FieldSchema(
            name="chunk_number",
            dtype=DataType.INT64
        ),
        FieldSchema(
            name="content",
            dtype=DataType.VARCHAR,
            max_length=65535
        ),
        FieldSchema(
            name="vector",
            dtype=DataType.FLOAT_VECTOR,
            dim=VECTOR_DIMENSION
        )
    ]

    return CollectionSchema(fields, description="Carbon registry sentence embeddings")