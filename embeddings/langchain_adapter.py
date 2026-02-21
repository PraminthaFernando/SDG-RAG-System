from langchain_core.embeddings import Embeddings

class LangChainEmbeddingAdapter(Embeddings):

    def __init__(self, embedding_model):
        self.embedding_model = embedding_model

    def embed_documents(self, texts):
        return self.embedding_model.embed_documents(texts)

    def embed_query(self, text):
        return self.embedding_model.embed_query(text)