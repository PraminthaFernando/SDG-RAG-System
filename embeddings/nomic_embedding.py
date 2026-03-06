from sentence_transformers import SentenceTransformer
from .base import BaseEmbedding
import warnings

warnings.filterwarnings("ignore", category=Warning)

class nomicEmbedding(BaseEmbedding):
    def __init__(self):
        self.model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True)
        
    def embed_documents(self, texts):
        prefixed_texts = ["search_document: " + t for t in texts]
        return self.model.encode(prefixed_texts, normalize_embeddings=True).tolist()

    def embed_query(self, text):
        prefixed_text = "search_query: " + text
        return self.model.encode([prefixed_text])[0].tolist()