"""
Generator Engine.

Generates executable Python code blocks from decisions.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.decision import Decision
from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.generation_context import GenerationContext
from mlos.generator.generators.base_generator import BaseGenerator


class GeneratorEngine:
    """
    Coordinates registered code generators to turn decisions into GeneratedCode.
    """

    def __init__(self, generators: list[BaseGenerator]):
        self.generators = generators

    def _get_decision_type(self, decision: Decision) -> str:
        title = decision.title.lower()
        if "missing value" in title:
            return "impute"
        elif "encoding" in title:
            return "encode"
        elif "scaling" in title:
            return "scale"
        elif "split" in title or "train/test" in title:
            return "split"
        elif "model" in title:
            return "model"
        return "unknown"

    def generate(
        self,
        context: GenerationContext,
    ) -> list[GeneratedCode]:
        """
        Map each decision in the context to its supporting generator and generate code.
        """
        generated = []
        registry = {gen.supported_decision_type: gen for gen in self.generators}

        for decision in context.decisions:
            dtype = self._get_decision_type(decision)
            generator = registry.get(dtype)
            if generator is not None:
                if generator.can_generate(decision):
                    generated.append(generator.generate(decision))

        return generated