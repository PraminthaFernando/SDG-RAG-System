from langchain_groq import ChatGroq
from langchain.agents import create_agent
import os

class BaseAgent:
    def __init__(self, model_name: str, temperature: float):
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name=model_name,
            temperature=temperature,
            max_tokens=4096
        )

        self.agent = create_agent(
            model=self.llm,
            tools=None
        )

    def invoke(self, prompt: str):
        response = self.agent.invoke({
            "messages": [{"role": "user", "content": prompt}]
        })

        message = response["messages"][-1].content
        return message