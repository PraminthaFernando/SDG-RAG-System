import torch
from typing import List
from transformers import AutoTokenizer, AutoModel

from .base import BaseEmbedding
from .utils import average_pool, normalize_embeddings
from .batching import batch_iterable

class E5Embedding(BaseEmbedding):

    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-large",
        batch_size: int = 32,
        max_length: int = 512
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size = batch_size
        self.max_length = max_length

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()

    # -------------------------------------
    # Core embedding logic
    # -------------------------------------
    def _embed_batch(self, texts: List[str]) -> torch.Tensor:

        encoded = self.tokenizer(
            texts,
            max_length=self.max_length,
            padding=True,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**encoded)

        embeddings = average_pool(
            outputs.last_hidden_state,
            encoded["attention_mask"]
        )

        embeddings = normalize_embeddings(embeddings)

        return embeddings.cpu()

    # -------------------------------------
    # Public API: Documents
    # -------------------------------------
    def embed_documents(self, texts: List[str]) -> List[List[float]]:

        prefixed_texts = ["passage: " + t for t in texts]

        all_embeddings = []

        for batch in batch_iterable(prefixed_texts, self.batch_size):
            batch_embeddings = self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings.tolist())

        return all_embeddings

    # -------------------------------------
    # Public API: Query
    # -------------------------------------
    def embed_query(self, text: str) -> List[float]:

        prefixed_text = "query: " + text
        embedding = self._embed_batch([prefixed_text])

        return embedding[0].tolist()