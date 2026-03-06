from .sdg_prompt_builder import SDGPromptBuilder
from .prototype_prompt_builder import PrototypePromptBuilder

class PromptBuilderFactory :
    @staticmethod
    def create(prompt_type: str = "prototype"):

        if prompt_type == "prototype":
            return PrototypePromptBuilder()
        
        if prompt_type == "questionie":
            return SDGPromptBuilder()

        raise ValueError(f"Unsupported prompt type: {prompt_type}")