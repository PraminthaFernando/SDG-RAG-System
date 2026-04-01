import torch
from sentence_transformers import CrossEncoder
from transformers import AutoModelForSequenceClassification, AutoTokenizer
# from optimum.onnxruntime import ORTModelForSequenceClassification  
from typing import List

class CrossEncoderReranker:

    def __init__(self, model_name="BAAI/bge-reranker-large"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained('BAAI/bge-reranker-base')
        # self.model_ort = ORTModelForSequenceClassification.from_pretrained('BAAI/bge-reranker-base', file_name="onnx/model.onnx")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # print(f"Run Reranker Model using: {self.device}")
        # self.model = CrossEncoder(model_name, device=str(self.device))

    def rerank(self, query: str, results: List[dict], top_k: int = 5) -> List[dict]:

        if not results:
            return []

        pairs = [(query, r["content"]) for r in results]
        
        encoded_input = self.tokenizer(pairs, padding=True, truncation=True, return_tensors='pt')

        # scores_ort = self.model_ort(**encoded_input, return_dict=True).logits.view(-1, ).float()
        # Compute token embeddings
        with torch.inference_mode():
            scores = self.model(**encoded_input, return_dict=True).logits.view(-1, ).float()

        # scores = self.model.predict(
        #     pairs,
        #     batch_size=32,
        #     show_progress_bar=False
        # )

        reranked = []

        for r, score in zip(results, scores):
            item = r.copy()
            item["rerank_score"] = float(score)
            reranked.append(item)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)

        return reranked[:top_k]