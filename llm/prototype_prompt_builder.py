from pathlib import Path
from typing import Tuple
from .utils import SDG_TARGETS

class PrototypePromptBuilder:
    def __init__(self):
        self.system_template = Path("llm/prompts/sdg_prototype_eval.txt").read_text()

    def build(self, sdg_key: str, target_code: str, evidence : str) -> str:
        
        target = ".".join(target_code.split(".")[:2])
        sdg_data = SDG_TARGETS[sdg_key]
        sdg_target_data = sdg_data["targets"][target]
        sdg_indicator_data = sdg_target_data["indicators"][target_code]
        sdg_goal = sdg_data["goal_description"]
        sdg_target = sdg_target_data["target_description"]
        sdg_indicator = sdg_indicator_data["indicator_description"]

        return self.system_template.format(
            sdg_key = sdg_key,
            sdg_goal = sdg_goal,
            target=target,
            sdg_target=sdg_target,
            indicator = target_code,
            sdg_indicator=sdg_indicator,
            evidences=evidence
        )