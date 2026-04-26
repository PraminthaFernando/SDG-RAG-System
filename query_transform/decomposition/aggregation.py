from pathlib import Path
from agents.judging_board import SDGJudgingBoard

class AnswerAggregator:
    def __init__(self):
        self.board = SDGJudgingBoard()
        self.prompt_template = Path(
            "query_transform/prompts/aggregation_prompt.txt"
        ).read_text()

    def aggregate(self, original_query, evidences, context) -> dict:
        
        evidences = "\n\n".join(evidences)

        return self.board.run(original_query, evidences, context)