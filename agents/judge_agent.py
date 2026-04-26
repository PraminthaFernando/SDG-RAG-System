import re
from .base_agent import BaseAgent
from .utils.retry import retry_llm
from .schemas.eval_schema import JudgeResult, DebateResult, Summary

class JudgeAgent(BaseAgent):
    def extract_json(self, text: str) -> str:
        if not text or not text.strip():
            raise ValueError("Empty LLM response")

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON found in response:\n{text}")

        return match.group(0)

    def parse_llm_output(self, raw, schema):
        """
        Universal parser for LLM outputs
        """

        if isinstance(raw, dict):
            return schema.model_validate(raw).model_dump()

        if isinstance(raw, str):
            clean = self.extract_json(raw)
            return schema.model_validate_json(clean).model_dump()

        raise TypeError(f"Unsupported LLM output type: {type(raw)}")

    @retry_llm()
    def initial_evaluate(self, prompt: str) -> dict:
        raw = self.invoke(prompt)
        result = self.parse_llm_output(raw, JudgeResult)
        return result

    @retry_llm()
    def debate(self, prompt: str) -> dict:
        raw = self.invoke(prompt)
        result = self.parse_llm_output(raw, DebateResult)
        return result
    
    @retry_llm()
    def get_summary(self, prompt: str) -> dict:
        raw = self.invoke(prompt)
        result = self.parse_llm_output(raw, Summary)
        return result