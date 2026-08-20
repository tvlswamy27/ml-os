"""
Assembly Service.

Coordinates in-memory compilation and workspace file writing.

Author: Vikram Tanakala
License: MIT
"""

from pathlib import Path

from mlos.cli.persistence import find_project_root
from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.pipeline import Pipeline
from mlos.domain.models.pipeline_source import PipelineSource
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.generator.assembler.pipeline_assembly_engine import PipelineAssemblyEngine


class AssemblyService:
    """
    Coordinates building and saving pipeline artifacts.
    """

    def __init__(
        self,
        assembly_engine: PipelineAssemblyEngine,
        project_memory_service: ProjectMemoryService,
    ):
        self.assembly_engine = assembly_engine
        self.project_memory_service = project_memory_service

    def assemble(
        self, memory: ProjectMemory, project_root: Path | str | None = None
    ) -> PipelineSource:
        """
        Assemble code list stored in ProjectMemory.generated_codes, save python pipeline,
        and update ProjectMemory.
        """
        generated_codes = memory.generated_codes
        if not generated_codes:
            # Empty decisions/generated_codes -> return empty PipelineSource with no exceptions
            source = PipelineSource(imports="", body="", code="")
            self.project_memory_service.update_pipeline_source(memory, source)
            return source

        # Compile in-memory pipeline source code
        source = self.assembly_engine.assemble(generated_codes)

        # Resolve paths
        project_dir = (
            Path(project_root) if project_root else (find_project_root() or Path.cwd())
        )
        artifacts_dir = project_dir / "artifacts"

        artifacts_dir.mkdir(parents=True, exist_ok=True)
        entrypoint_path = artifacts_dir / "pipeline.py"

        # Resolve dataset path for pipeline script execution to an absolute path
        dataset_path_str = ""
        if memory.dataset and memory.dataset.path:
            dataset_path_str = str(Path(memory.dataset.path).resolve().as_posix())

        loader_code = ""
        if dataset_path_str:
            suffix = Path(dataset_path_str).suffix.lower()
            read_func = "read_parquet" if suffix == ".parquet" else "read_csv"
            loader_code = f"""import pandas as pd
df = pd.{read_func}("{dataset_path_str}")
"""

        # Write execution pipeline
        has_model = False
        has_split = False
        for gc in generated_codes:
            if "model =" in gc.code or "model.fit" in gc.code:
                has_model = True
            if "test_df" in gc.code:
                has_split = True

        eval_code = ""
        if has_model:
            target = memory.dataset.target if (memory.dataset and memory.dataset.target) else "target"
            prob_type = "Classification"
            if memory.project_profile and memory.project_profile.problem_type:
                prob_type = memory.project_profile.problem_type
            elif memory.dataset and memory.dataset.problem_type:
                prob_type = memory.dataset.problem_type

            df_name = "test_df" if has_split else "df"
            eval_code = f"""
# ==========================================
# Post-training artifact generation
# ==========================================
import joblib
import json
from pathlib import Path

# Evaluate on test set
X_test = {df_name}.drop(columns=["{target}"])
y_test = {df_name}["{target}"]
preds = model.predict(X_test)

metrics = {{}}
if "{prob_type}".lower() == "classification":
    from sklearn.metrics import accuracy_score, precision_score, recall_score
    metrics["accuracy"] = float(accuracy_score(y_test, preds))
    metrics["precision"] = float(precision_score(y_test, preds, average="weighted", zero_division=0))
    metrics["recall"] = float(recall_score(y_test, preds, average="weighted", zero_division=0))
else:
    import numpy as np
    from sklearn.metrics import mean_squared_error, r2_score
    mse = mean_squared_error(y_test, preds)
    metrics["rmse"] = float(np.sqrt(mse))
    metrics["r2"] = float(r2_score(y_test, preds))

# Save model and metrics to artifacts folder
artifacts_dir = Path("artifacts")
artifacts_dir.mkdir(exist_ok=True)

joblib.dump(model, artifacts_dir / "model.joblib")

with open(artifacts_dir / "metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

# Save explainability/importance
import numpy as np
if hasattr(model, "feature_importances_"):
    importances = model.feature_importances_
elif hasattr(model, "coef_"):
    importances = np.abs(model.coef_)
    if importances.ndim > 1:
        importances = importances.mean(axis=0)
else:
    importances = np.ones(len(X_test.columns)) / len(X_test.columns)

sorted_importance = {{name: float(imp) for name, imp in zip(X_test.columns, importances)}}
sorted_importance = dict(sorted(sorted_importance.items(), key=lambda x: x[1], reverse=True))

with open(artifacts_dir / "explainability_importance.json", "w") as f:
    json.dump(sorted_importance, f, indent=2)
"""

        full_code = loader_code + "\n" + source.code + "\n" + eval_code
        entrypoint_path.write_text(full_code, encoding="utf-8")

        # Instantiate Pipeline domain model and record to ProjectMemory
        pipeline = Pipeline(entrypoint_path=entrypoint_path.resolve())
        self.project_memory_service.update_pipeline(memory, pipeline)
        self.project_memory_service.update_pipeline_source(memory, source)

        return source

    def run_assembly(
        self,
        memory: ProjectMemory,
        generated_codes: list[GeneratedCode],
    ) -> None:
        """
        Backward compatible run_assembly delegation.
        """
        self.project_memory_service.update_generated_codes(memory, generated_codes)
        self.assemble(memory)
