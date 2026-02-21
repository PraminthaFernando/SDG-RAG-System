import os
from typing import Any
from .base_llm import BaseLLM
from .config import LLM_MODEL_NAME, LLM_TEMPERATURE, LLM_MAX_TOKENS
from langchain_groq import ChatGroq
from .models import SDG7Evidence

class GroqLLMClient(BaseLLM):

    def __init__(self, temperature):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment.")

        self.model = ChatGroq(
            api_key=self.api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=temperature,
            verbose=False
        )
        self.schema = SDG7Evidence

    def generate(self, prompt: str) -> Any:
        
        structured_model = self.model.with_structured_output(self.schema)

        response = structured_model.invoke(prompt)

        return response