from sentence_transformers import SentenceTransformer
from .base import BaseEmbedding
import warnings

warnings.filterwarnings("ignore", category=Warning)

class BGEEmbedding(BaseEmbedding):
    def __init__(self):
        self.model = SentenceTransformer("BAAI/bge-large-en-v1.5")
        
    def embed_documents(self, texts):
        return self.model.encode(
            texts, 
            normalize_embeddings=True
        ).tolist()

    def embed_query(self, text):
        return self.model.encode(
            [text], 
            normalize_embeddings=True
        )[0].tolist()