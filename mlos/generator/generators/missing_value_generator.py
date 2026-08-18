"""
Missing Value Generator.

Generates Python code for handling missing values.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.decision import Decision
from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.generation_context import GenerationContext
from mlos.generator.generators.base_generator import BaseGenerator


class MissingValueGenerator(BaseGenerator):

    @property
    def supported_decision_type(self) -> str:
        return "impute"

    def can_generate(
        self,
        decision: Decision,
    ) -> bool:

        return decision.title.startswith("Missing Value")

    def generate(
        self,
        decision: Decision,
        context: GenerationContext | None = None,
    ) -> GeneratedCode:

        if decision.columns:
            column = decision.columns[0]
        else:
            column = decision.title.split(": ")[-1] if ": " in decision.title else "COLUMN_NAME"

        strategy = decision.strategy
        imports = []
        code = ""

        if strategy == "Median Imputation":
            imports = ["from sklearn.impute import SimpleImputer"]
            code = f"""
imputer = SimpleImputer(strategy="median")
df[['{column}']] = imputer.fit_transform(df[['{column}']])
""".strip()
        elif strategy == "Mode Imputation":
            imports = ["from sklearn.impute import SimpleImputer"]
            code = f"""
imputer = SimpleImputer(strategy="most_frequent")
df[['{column}']] = imputer.fit_transform(df[['{column}']])
""".strip()
        elif strategy == "Mean Imputation":
            imports = ["from sklearn.impute import SimpleImputer"]
            code = f"""
imputer = SimpleImputer(strategy="mean")
df[['{column}']] = imputer.fit_transform(df[['{column}']])
""".strip()
        elif strategy == "drop":
            code = f"df = df.drop(columns=['{column}'])"
        else:
            code = f"# No generator available for strategy: {strategy}."

        return GeneratedCode(
            title=decision.title,
            description=decision.reason,
            imports=imports,
            code=code,
        )
