"""
Model Generator.

Generates Python code for model selection and training.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.decision import Decision
from mlos.domain.models.generated_code import GeneratedCode
from mlos.generator.generators.base_generator import BaseGenerator


class ModelGenerator(BaseGenerator):

    @property
    def supported_decision_type(self) -> str:
        return "model"

    def can_generate(self, decision: Decision) -> bool:
        return "model" in decision.title.lower()

    def generate(self, decision: Decision) -> GeneratedCode:
        imports = ["from sklearn.ensemble import RandomForestClassifier"]
        code = """
model = RandomForestClassifier()
# Model training implementation
""".strip()
        return GeneratedCode(
            title=decision.title,
            description=decision.reason,
            imports=imports,
            code=code,
        )
