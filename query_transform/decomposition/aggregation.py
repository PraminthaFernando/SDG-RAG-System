from pathlib import Path
from agents.sdg_agent import SDGAgent

class AnswerAggregator:
    def __init__(self):
        self.agent = SDGAgent()
        self.prompt_template = Path(
            "query_transform/prompts/aggregation_prompt.txt"
        ).read_text()

    def aggregate(self, original_query, sub_answers, context) -> dict:

        prompt = self.prompt_template.format(
            original_query=original_query,
            combined=sub_answers,
            context=context
        )

        return self.agent.run(prompt)