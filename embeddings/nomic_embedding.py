from sentence_transformers import SentenceTransformer
from .base import BaseEmbedding
import warnings
import torch

warnings.filterwarnings("ignore", category=Warning)

class nomicEmbedding(BaseEmbedding):
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Run Nomic Embedding Model using: {self.device}")
        self.model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True, device=str(self.device))
        
    def embed_documents(self, texts):
        prefixed_texts = ["search_document: " + t for t in texts]
        return self.model.encode(prefixed_texts, normalize_embeddings=True).tolist()

    def embed_query(self, text):
        prefixed_text = "search_query: " + text
        return self.model.encode([prefixed_text])[0].tolist()