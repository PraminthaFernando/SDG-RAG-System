import os
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from agents.tools.url_fetch_tool import fetch_verified_url
from llm.models import SDGEvaluationResult

class SDGAgent:
    def __init__(self, web_tool : bool = False):
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name=os.getenv("GROQ_MODEL_NAME"),
            temperature=0,
            max_tokens=4096
        )
        
        if web_tool:
            self.tools = [fetch_verified_url]
            self.agent = create_agent(
                model=self.llm,
                tools=self.tools
            )
        
        else :
            self.agent = create_agent(
                model=self.llm
            )

    def run(self, question: str):
        return self.agent.invoke({"messages": [{"role": "user", "content": question}]})