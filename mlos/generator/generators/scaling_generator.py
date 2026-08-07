"""
Scaling Generator.

Generates Python code for feature scaling.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.decision import Decision
from mlos.domain.models.generated_code import GeneratedCode
from mlos.generator.generators.base_generator import BaseGenerator


class ScalingGenerator(BaseGenerator):

    @property
    def supported_decision_type(self) -> str:
        return "scale"

    def can_generate(self, decision: Decision) -> bool:
        return "scaling" in decision.title.lower()

    def generate(self, decision: Decision) -> GeneratedCode:
        imports = ["from sklearn.preprocessing import StandardScaler"]
        code = """
scaler = StandardScaler()
# Scaler implementation
""".strip()
        return GeneratedCode(
            title=decision.title,
            description=decision.reason,
            imports=imports,
            code=code,
        )
