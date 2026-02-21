from abc import ABC, abstractmethod
from typing import List

class BaseRetriever(ABC):

    @abstractmethod
    def retrieve(self, query: str, pid: int = None, top_k: int = 5) -> List[dict]:
        pass