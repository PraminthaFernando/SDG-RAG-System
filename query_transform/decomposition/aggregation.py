from pathlib import Path
from agents.sdg_agent import SDGAgent

class AnswerAggregator:
    def __init__(self):
        self.agent = SDGAgent()
        self.prompt_template = Path(
            "query_transform/prompts/aggregation_prompt.txt"
        ).read_text()

    def aggregate(self, stepback_query, blocks, original_query) -> dict:

        evidences = "\n\n".join(blocks)

        prompt = self.prompt_template.format(
            original_query=original_query,
            stepback_query=stepback_query,
            evidences=evidences,
        )

        return self.agent.run(prompt)