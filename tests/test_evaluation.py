"""
Unit and integration tests for the ML-OS Evaluation Subsystem.
"""

import json
from datetime import datetime
from pathlib import Path

from mlos.domain.models.evaluation_artifacts import EvaluationArtifacts
from mlos.domain.models.evaluation_result import EvaluationResult
from mlos.domain.models.execution_result import ExecutionResult
from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.services.evaluation_service import EvaluationService
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.engine.engine import MLOSEngine
from mlos.evaluation.evaluation_engine import EvaluationEngine
from mlos.evaluation.evaluators.simple_evaluator import SimpleEvaluator


def test_evaluation_artifacts():
    artifacts = EvaluationArtifacts(metrics={"accuracy": 0.85})
    assert artifacts.metrics["accuracy"] == 0.85


def test_evaluation_result_passed_flag():
    # Zero checks -> passes by default
    res_no_checks = EvaluationResult(metrics={"accuracy": 0.85})
    assert res_no_checks.passed is True

    # All checks True -> passes
    res_pass = EvaluationResult(
        metrics={"accuracy": 0.85, "loss": 0.2},
        checks={"accuracy_gate": True, "loss_gate": True},
    )
    assert res_pass.passed is True

    # One check False -> fails
    res_fail = EvaluationResult(
        metrics={"accuracy": 0.72, "loss": 0.2},
        checks={"accuracy_gate": False, "loss_gate": True},
    )
    assert res_fail.passed is False


def test_simple_evaluator_direct_artifacts():
    artifacts = EvaluationArtifacts(metrics={"accuracy": 0.88, "loss": 0.15})
    exec_result = ExecutionResult(status="SUCCESS", start_time=datetime.now())

    evaluator = SimpleEvaluator()
    assert evaluator.can_evaluate(artifacts, exec_result) is True

    res = evaluator.evaluate(artifacts, exec_result)
    assert res.metrics["accuracy"] == 0.88
    assert res.metrics["loss"] == 0.15
    assert res.checks["accuracy_threshold_passed"] is True
    assert res.checks["loss_threshold_passed"] is True
    assert res.passed is True


def test_simple_evaluator_stdout_fallback():
    # Empty artifacts dict
    artifacts = EvaluationArtifacts()
    # Stdout with metric formats
    exec_result = ExecutionResult(
        status="SUCCESS",
        start_time=datetime.now(),
        stdout="Epoch 1/5\nAccuracy: 0.78\nLoss: 0.58\n",
    )

    evaluator = SimpleEvaluator()
    assert evaluator.can_evaluate(artifacts, exec_result) is True

    res = evaluator.evaluate(artifacts, exec_result)
    assert res.metrics["accuracy"] == 0.78
    assert res.metrics["loss"] == 0.58
    assert res.checks["accuracy_threshold_passed"] is False  # 0.78 < 0.80
    assert res.checks["loss_threshold_passed"] is False  # 0.58 > 0.50
    assert res.passed is False


def test_evaluation_engine_consolidation():
    engine = EvaluationEngine()
    engine.register_evaluator(SimpleEvaluator())

    artifacts = EvaluationArtifacts(metrics={"accuracy": 0.95})
    exec_result = ExecutionResult(status="SUCCESS", start_time=datetime.now())

    res = engine.evaluate(artifacts, exec_result)
    assert res.metrics["accuracy"] == 0.95
    assert res.checks["accuracy_threshold_passed"] is True
    assert res.passed is True


def test_evaluation_service_structured_file(tmp_path):
    memory = ProjectMemory(
        project_name="EvaluationProj", project_goal="Test evaluation"
    )
    memory.execution_result = ExecutionResult(
        status="SUCCESS", start_time=datetime.now()
    )

    # Build workspace artifacts metrics.json
    project_dir = Path("playground") / "EvaluationProj"
    artifacts_dir = project_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    metrics_file = artifacts_dir / "metrics.json"
    metrics_file.write_text(json.dumps({"accuracy": 0.82, "loss": 0.35}))

    engine = EvaluationEngine()
    engine.register_evaluator(SimpleEvaluator())
    memory_service = ProjectMemoryService()
    service = EvaluationService(
        evaluation_engine=engine, project_memory_service=memory_service
    )

    service.run_evaluation(memory)

    assert memory.evaluation_result is not None
    assert memory.evaluation_result.metrics["accuracy"] == 0.82
    assert memory.evaluation_result.metrics["loss"] == 0.35
    assert memory.evaluation_result.checks["accuracy_threshold_passed"] is True
    assert memory.evaluation_result.passed is True

    # Clean up project dir
    if project_dir.exists():
        import shutil

        shutil.rmtree(project_dir)


def test_full_pipeline_assemble_execute_evaluate_integration(tmp_path):
    # Setup MLOSEngine
    engine = MLOSEngine()
    engine.create_project(name="FullRunProj", goal="Verify compile run and evaluate")

    # We will generate a python script that writes a structured metrics.json file to its own artifacts path!
    project_dir = Path("playground") / "FullRunProj"

    script_code = """
import os
import json

# Setup output path
artifacts_dir = os.path.join("playground", "FullRunProj", "artifacts")
os.makedirs(artifacts_dir, exist_ok=True)

# Write output file
metrics = {"accuracy": 0.91, "loss": 0.19}
with open(os.path.join(artifacts_dir, "metrics.json"), "w") as f:
    json.dump(metrics, f)

print("Stdout accuracy: 0.91")
"""

    gc = GeneratedCode(
        title="TrainingStep",
        description="Fit model and save stats",
        imports=[],
        code=script_code,
    )

    # 1. Assemble
    engine.assemble([gc])

    # 2. Execute
    engine.execute()

    # 3. Evaluate
    engine.evaluate()

    # 4. Verify Results
    eval_result = engine.project_memory.evaluation_result
    assert eval_result is not None
    assert eval_result.metrics["accuracy"] == 0.91
    assert eval_result.metrics["loss"] == 0.19
    assert eval_result.checks["accuracy_threshold_passed"] is True
    assert eval_result.checks["loss_threshold_passed"] is True
    assert eval_result.passed is True

    # Clean up
    if project_dir.exists():
        import shutil

        shutil.rmtree(project_dir)
