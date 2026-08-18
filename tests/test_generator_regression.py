import os
import shutil
from pathlib import Path
import pytest

from mlos.domain.models.decision import Decision
from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.dataset import Dataset
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.generation_context import GenerationContext
from mlos.generator.generators.missing_value_generator import MissingValueGenerator
from mlos.generator.generators.scaling_generator import ScalingGenerator
from mlos.generator.generators.model_generator import ModelGenerator
from mlos.engine.engine import MLOSEngine


def test_missing_value_generator_uses_correct_column():
    generator = MissingValueGenerator()
    decision = Decision(
        title="Missing Value Strategy: Age",
        strategy="Median Imputation",
        confidence="High",
        reason="Impute missing age",
        columns=["Age"],
    )
    res = generator.generate(decision)
    assert "df[['Age']]" in res.code
    assert "COLUMN_NAME" not in res.code


def test_scaling_generator_uses_correct_columns():
    generator = ScalingGenerator()
    decision = Decision(
        title="Scaling Strategy: global",
        strategy="StandardScaler",
        confidence="High",
        reason="Scale Age and Fare",
        columns=["Age", "Fare"],
    )
    res = generator.generate(decision)
    assert "df[['Age', 'Fare']]" in res.code
    assert "COLUMN_NAME" not in res.code


def test_model_generator_uses_correct_model_and_params():
    generator = ModelGenerator()
    decision = Decision(
        title="Model Selection: Random Forest Classifier",
        strategy="random_forest_classifier",
        confidence="High",
        reason="Winning candidate",
        columns=["Survived"],
        parameters={"n_estimators": 150, "max_depth": 10},
    )
    memory = ProjectMemory(project_name="TestProj", project_goal="Test")
    memory.dataset = Dataset(path="playground/sample.csv", target="Survived", problem_type="Classification")
    context = GenerationContext(project_memory=memory, decisions=(decision,))
    
    res = generator.generate(decision, context)
    assert "RandomForestClassifier(n_estimators=150, random_state=42, max_depth=10)" in res.code
    assert "X = df.drop(columns=['Survived'])" in res.code
    assert "y = df['Survived']" in res.code


def test_end_to_end_assembled_pipeline_runs_correctly():
    # Initialize Engine and test project workspace
    engine = MLOSEngine()
    project_dir = Path("playground") / "RegressionProj"
    if project_dir.exists():
        shutil.rmtree(project_dir)

    engine.create_project(
        name="RegressionProj",
        goal="Verify dynamic code generation",
        destination=str(project_dir),
    )

    # 1. Load dataset metadata via analyzer
    dataset_path = "playground/sample.csv"
    df = engine.data_loader.load(dataset_path)
    engine.project_memory.dataset = engine.dataset_analyzer.analyze(df, target="Survived")
    engine.project_memory.dataset.path = dataset_path

    # 2. Add default preprocessors decisions manually or via decide()
    preprocessors_decisions = engine.decide()
    # Check that scaling decision defaults numerical columns
    scaling_dec = next((d for d in preprocessors_decisions if "scaling" in d.title.lower()), None)
    assert scaling_dec is not None
    assert "Age" in scaling_dec.columns
    assert "Fare" in scaling_dec.columns

    # 3. Run automl to select winning estimator and generate structured model decision
    engine.run_automl(
        dataset_path,
        target_column="Survived",
        output_dir=str(project_dir / "artifacts" / "automl"),
        experiment_id="test_exp",
        workspace_root=project_dir,
    )

    # Verify model decision was created and registered
    decisions = engine.project_memory.decisions
    model_dec = next((d for d in decisions if "model" in d.title.lower()), None)
    assert model_dec is not None
    assert model_dec.strategy in ["random_forest_classifier", "logistic_regression", "extra_trees_classifier", "decision_tree_classifier"]
    assert model_dec.columns == ["Survived"]

    # 4. Generate pipeline python codes
    generated_codes = engine.generate()
    assert len(generated_codes) > 0

    # 5. Assemble pipeline script
    engine.assemble(generated_codes)
    pipeline_file = project_dir / "artifacts" / "pipeline.py"
    assert pipeline_file.exists()

    content = pipeline_file.read_text(encoding="utf-8")
    assert "COLUMN_NAME" not in content
    assert "Survived" in content
    # Verify exact pandas loader logic without COLUMN_NAME hack
    assert 'df["COLUMN_NAME"] = df.iloc[:, 1]' not in content

    # 6. Execute the assembled script in a subprocess
    session = engine.execute()
    assert session is not None
    assert session.status == "SUCCESS"
    assert session.exit_code == 0

    # Clean up project
    if project_dir.exists():
        shutil.rmtree(project_dir)
