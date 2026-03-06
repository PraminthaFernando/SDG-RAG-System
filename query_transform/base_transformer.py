from abc import ABC, abstractmethod
from typing import List

class BaseQueryTransformer(ABC):

    @abstractmethod
    def transform(self, query: str) -> List[str]:
        pass