from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
from .base import BaseEmbedding
import warnings

warnings.filterwarnings("ignore", category=Warning)

class simCSEEmbedding(BaseEmbedding):
    def __init__(self):
        self.model = SentenceTransformer("princeton-nlp/sup-simcse-roberta-large")
        
    def embed_documents(self, texts):
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text):
        return self.model.encode([text], normalize_embeddings=True)[0].tolist()