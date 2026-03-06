from .e5_embedding import E5Embedding
from .remort_embedding import RemoteEmbedding
from .simCSE_embedding import simCSEEmbedding
from .bge_Embedding import BGEEmbedding
from .nomic_embedding import nomicEmbedding

class EmbeddingFactory:

    @staticmethod
    def create(model_type: str = "e5", **kwargs):

        if model_type == "e5":
            return E5Embedding(**kwargs)
        
        if model_type == "remort":
            return RemoteEmbedding(**kwargs)
        
        if model_type == "simCSE":
            return simCSEEmbedding()
        
        if model_type == "bge":
            return BGEEmbedding()
        
        if model_type == "nomic":
            return nomicEmbedding()

        raise ValueError(f"Unsupported embedding type: {model_type}")