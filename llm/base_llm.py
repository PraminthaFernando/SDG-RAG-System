from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any

class BaseLLM(ABC):

    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass
    
    @abstractmethod
    def generate_structured(self, prompt, schema : type[BaseModel]) -> Any:
        pass