from pathlib import Path
from typing import List
from .llm_client import GroqLLMClient

class EvidenceRefiner:

    def __init__(self):
        self.client = GroqLLMClient()
        self.prompt_path = Path("llm/prompts/evidence_refinement.txt")

    def refine(self, evidence: List[str]) -> List[str]:

        prompt_template = self.prompt_path.read_text()

        formatted_prompt = prompt_template.format(
            evidence="\n".join(evidence)
        )

        response = self.client.generate(formatted_prompt)

        return response.get("cleaned_evidences")