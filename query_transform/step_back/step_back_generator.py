from pathlib import Path

class StepBackGenerator:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.prompt_template = Path(
            "query_transform/prompts/step_back_prompt.txt"
        ).read_text()

    def generate(self, query: str) -> str:
        prompt = self.prompt_template.format(query=query)
        response = self.llm.generate(prompt)
        return response.strip()