"""
Missing Value Generator.

Generates Python code for handling missing values.

Author: Vikram Tanakala
License: MIT
"""

from mlos.generator.generators.base_generator import BaseGenerator

from mlos.domain.models.decision import Decision
from mlos.domain.models.generated_code import GeneratedCode


class MissingValueGenerator(BaseGenerator):

    def can_generate(
        self,
        decision: Decision,
    ) -> bool:

        return decision.title.startswith(
            "Missing Value"
        )

    def generate(
        self,
        decision: Decision,
    ) -> GeneratedCode:

        if decision.strategy == "Median Imputation":

            imports = [
                "from sklearn.impute import SimpleImputer",
            ]

            code = """
imputer = SimpleImputer(
    strategy="median",
)

df["COLUMN_NAME"] = imputer.fit_transform(
    df[["COLUMN_NAME"]]
)
""".strip()

        elif decision.strategy == "Mode Imputation":

            imports = [
                "from sklearn.impute import SimpleImputer",
            ]

            code = """
imputer = SimpleImputer(
    strategy="most_frequent",
)

df["COLUMN_NAME"] = imputer.fit_transform(
    df[["COLUMN_NAME"]]
)
""".strip()

        else:

            imports = []

            code = "# No generator available."

        return GeneratedCode(
            title=decision.title,
            description=decision.reason,
            imports=imports,
            code=code,
        )