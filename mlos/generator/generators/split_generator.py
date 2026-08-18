"""
Split Generator.

Generates Python code for train/test splitting.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.decision import Decision
from mlos.domain.models.generated_code import GeneratedCode
from mlos.generator.generators.base_generator import BaseGenerator


class SplitGenerator(BaseGenerator):

    @property
    def supported_decision_type(self) -> str:
        return "split"

    def can_generate(self, decision: Decision) -> bool:
        return "split" in decision.title.lower()

    def generate(
        self,
        decision: Decision,
        context = None,
    ) -> GeneratedCode:
        imports = ["from sklearn.model_selection import train_test_split"]
        code = """
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
""".strip()
        return GeneratedCode(
            title=decision.title,
            description=decision.reason,
            imports=imports,
            code=code,
        )
