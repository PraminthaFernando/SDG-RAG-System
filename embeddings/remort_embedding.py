import requests
from typing import List
from .base import BaseEmbedding
from .config import ENDPOINTS
import time

class RemoteEmbedding(BaseEmbedding):

    def __init__(
        self,
        endpoint: str = "ngrok",
        timeout: int = 60,
        max_retries: int = 3
    ):
        try:
            self.api_url = ENDPOINTS[endpoint].rstrip("/")
        except KeyError:
            raise ValueError(f"Unknown endpoint: {endpoint}")
            
        self.timeout = timeout
        self.max_retries = max_retries

    def _post(self, payload: dict):

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.api_url}/embed",
                    json=payload,
                    timeout=self.timeout
                )

                # Check HTTP status
                if response.status_code != 200:
                    raise RuntimeError(
                        f"Embedding API returned "
                        f"{response.status_code}: {response.text}"
                    )

                # Ensure JSON response
                try:
                    data = response.json()
                except ValueError:
                    raise RuntimeError(
                        f"Invalid JSON response: {response.text}"
                    )

                if "embeddings" not in data:
                    raise RuntimeError(
                        f"'embeddings' key missing in response: {data}"
                    )

                return data["embeddings"]

            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    raise RuntimeError("Embedding API timeout.")
                time.sleep(2)

            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Request failed: {str(e)}")
                time.sleep(2)

        raise RuntimeError("Embedding request failed after retries.")

    def embed_documents(self, texts: List[str]):
        if not texts:
            return []

        batch_size = 128
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            embeddings = self._post({"texts": batch})
            all_embeddings.extend(embeddings)

        return all_embeddings
    
    def embed_query(self, text: str):
        embeddings = self.embed_documents([text])
        return embeddings[0]