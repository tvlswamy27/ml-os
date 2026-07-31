"""
Encoding Generator.

Generates Python code for encoding categorical columns.

Author: Vikram Tanakala
License: MIT
"""

from mlos.generator.generators.base_generator import BaseGenerator
from mlos.domain.models.decision import Decision
from mlos.domain.models.generated_code import GeneratedCode


class EncodingGenerator(BaseGenerator):

    @property
    def supported_decision_type(self) -> str:
        return "encode"

    def can_generate(self, decision: Decision) -> bool:
        return "encoding" in decision.title.lower()

    def generate(self, decision: Decision) -> GeneratedCode:
        # Extract column name from title, e.g. "Encoding Strategy: col1"
        parts = decision.title.split(":")
        column_name = parts[1].strip() if len(parts) > 1 else "COLUMN_NAME"

        if decision.strategy == "One-Hot Encoding":
            imports = ["import pandas as pd"]
            code = f'df = pd.get_dummies(df, columns=["{column_name}"])'
        elif decision.strategy == "Label Encoding":
            imports = ["from sklearn.preprocessing import LabelEncoder"]
            code = f"""
le = LabelEncoder()
df["{column_name}"] = le.fit_transform(df["{column_name}"])
""".strip()
        else:
            imports = []
            code = "# No encoding generator available."

        return GeneratedCode(
            title=decision.title,
            description=decision.reason,
            imports=imports,
            code=code,
        )
