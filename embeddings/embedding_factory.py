from .e5_embedding import E5Embedding
from .remort_embedding import RemoteEmbedding

class EmbeddingFactory:

    @staticmethod
    def create(model_type: str = "e5", **kwargs):

        if model_type == "e5":
            return E5Embedding(**kwargs)
        
        if model_type == "remort":
            return RemoteEmbedding(**kwargs)

        raise ValueError(f"Unsupported embedding type: {model_type}")