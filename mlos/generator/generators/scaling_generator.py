"""
Scaling Generator.

Generates Python code for feature scaling.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.decision import Decision
from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.generation_context import GenerationContext
from mlos.generator.generators.base_generator import BaseGenerator


class ScalingGenerator(BaseGenerator):

    @property
    def supported_decision_type(self) -> str:
        return "scale"

    def can_generate(self, decision: Decision) -> bool:
        return "scaling" in decision.title.lower()

    def generate(
        self,
        decision: Decision,
        context: GenerationContext | None = None,
    ) -> GeneratedCode:
        strategy = decision.strategy
        cols = decision.columns or []

        if strategy == "MinMaxScaler":
            imports = ["from sklearn.preprocessing import MinMaxScaler"]
            scaler_init = "MinMaxScaler()"
        elif strategy == "RobustScaler":
            imports = ["from sklearn.preprocessing import RobustScaler"]
            scaler_init = "RobustScaler()"
        else:
            imports = ["from sklearn.preprocessing import StandardScaler"]
            scaler_init = "StandardScaler()"

        if cols:
            cols_str = ", ".join(f"'{c}'" for c in cols)
            code = f"""
scaler = {scaler_init}
df[[{cols_str}]] = scaler.fit_transform(df[[{cols_str}]])
""".strip()
        else:
            code = "# No columns selected for scaling."

        return GeneratedCode(
            title=decision.title,
            description=decision.reason,
            imports=imports,
            code=code,
        )
