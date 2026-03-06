from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from .llm_client import GroqLLMClient
from pydantic import PrivateAttr

class LangChainGroqLLM(BaseChatModel):
    _client: GroqLLMClient = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._client = GroqLLMClient(temperature=0.1)

    def _generate(self, messages, stop=None):
        prompt = messages[-1].content
        response = self._client.generate(prompt)
        return AIMessage(content=response)

    @property
    def _llm_type(self) -> str:
        return "groq"