from pymilvus import (
    FieldSchema,
    CollectionSchema,
    DataType
)
from .config import VECTOR_DIMENSIONS


def create_schema(model : str = "e5", collection : str = "e5"):
    fields = [
        FieldSchema(
            name="id",
            dtype=DataType.VARCHAR,
            is_primary=True,
            auto_id=False,
            max_length=200
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
        )
    ]
    
    if collection == "policy_docs":
        fields.append(
            FieldSchema(
            name="vector",
            dtype=DataType.FLOAT_VECTOR,
            dim=VECTOR_DIMENSIONS[model]
        )
        )
        return CollectionSchema(
            fields=fields,
            description="SDG policy sentence embeddings"
        )
        
    modified  = [
        FieldSchema(
            name="pid",
            dtype=DataType.VARCHAR,
            max_length=20
        ),
        FieldSchema(
            name="vector",
            dtype=DataType.FLOAT_VECTOR,
            dim=VECTOR_DIMENSIONS[model]
        )
    ]

    fields.extend(modified)

    return CollectionSchema(
        fields=fields,
        description="Carbon registry sentence embeddings"
    )