"""
Model Generator.

Generates Python code for model selection and training.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.decision import Decision
from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.generation_context import GenerationContext
from mlos.generator.generators.base_generator import BaseGenerator


class ModelGenerator(BaseGenerator):

    @property
    def supported_decision_type(self) -> str:
        return "model"

    def can_generate(self, decision: Decision) -> bool:
        return "model" in decision.title.lower()

    def generate(
        self,
        decision: Decision,
        context: GenerationContext | None = None,
    ) -> GeneratedCode:
        from mlos.models.catalog import ModelCatalog

        meta = ModelCatalog.get(decision.strategy)

        if meta:
            module_path = meta.module_path
            class_name = meta.class_name
            imports = [f"from {module_path} import {class_name}"]

            # Combine defaults with actual selected parameters if available
            params = dict(meta.default_parameters)
            if decision.parameters:
                params.update(decision.parameters)

            # Construct the parameters string for instantiation
            param_parts = []
            for k, v in params.items():
                if isinstance(v, str):
                    param_parts.append(f"{k}='{v}'")
                else:
                    param_parts.append(f"{k}={v}")
            param_str = ", ".join(param_parts)

            target = context.target_column if context else "target"

            # Check if dataset splitting was generated (we can check context or decision list)
            # Default to train_df if split is present, else fall back to df
            has_split = False
            if context:
                for dec in context.decisions:
                    if "split" in dec.title.lower():
                        has_split = True
                        break
            
            df_name = "train_df" if has_split else "df"

            code = f"""
# Model selection: {meta.name}
model = {class_name}({param_str})

# Prepare features and target
X = {df_name}.drop(columns=['{target}'])
y = {df_name}['{target}']

model.fit(X, y)
""".strip()
        else:
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
