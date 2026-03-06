from pathlib import Path
from langchain_core.prompts import PromptTemplate

class SDGPromptBuilder:
    def __init__(self):
        self.template = Path("llm/prompts/sdg_evaluation.txt").read_text()

    def build(self, sdg_label: str, question: str, context: str) -> str:

        return self.template.format(
            sdg=sdg_label,
            question=question,
            context=context
        )