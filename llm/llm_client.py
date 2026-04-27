import os
import json
from typing import Optional
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

from .base_llm import BaseLLM
from dotenv import load_dotenv
load_dotenv()


class GroqLLMClient(BaseLLM):
    def __init__(self, temperature: float = 0.0):

        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment.")

        self.model = ChatGroq(
            api_key=self.api_key,
            model_name=os.getenv("GROQ_MODEL_NAME"),
            temperature=temperature,
            verbose=False,
            max_tokens=4096,
            max_retries=3
        )

    # 🔥 BACKWARD COMPATIBILITY FIX
    def invoke(self, prompt):
        """
        Supports old code that calls llm.invoke(...)
        """
        return self.generate(prompt=prompt)

    def generate(
        self,
        prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None
    ) -> str:

        chain = self.model | StrOutputParser()

        if prompt is not None:
            return chain.invoke(prompt)

        messages = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        if user_prompt:
            messages.append(HumanMessage(content=user_prompt))

        return chain.invoke(messages)

    def generate_structured(
        self,
        schema: type[BaseModel],
        prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None
    ) -> BaseModel:

        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                messages = []

                if system_prompt:
                    messages.append(SystemMessage(content=system_prompt))

                if user_prompt:
                    messages.append(HumanMessage(content=user_prompt))

                if prompt:
                    messages.append(HumanMessage(content=prompt))

                response = self.model.invoke(messages)
                content = response.content.strip()

                # Clean markdown JSON wrappers
                content = content.replace("```json", "").replace("```", "").strip()

                parsed = json.loads(content)

                return schema.model_validate(parsed)

            except Exception as e:
                print(f"[Retry {attempt+1}/{max_attempts}] JSON parsing failed: {e}")

        fallback = {
            "evidences": [],
            "justification": "Model output could not be parsed after retries.",
            "score": 0
        }

        return schema.model_validate(fallback)