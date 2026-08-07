"""
Unit and integration tests for LLM Reflection subsystem.

Author: Antigravity
License: MIT
"""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mlos.domain.models.knowledge_summary import ActiveRuleSummary, KnowledgeSummary
from mlos.domain.models.reflection.reflection_context import (
    EvaluationSummary,
    ExecutionSummary,
    PlanningSummary,
    ReflectionContext,
)
from mlos.domain.models.reflection.reflection_session import ReflectionSession
from mlos.domain.models.reflection.reflection_telemetry import ReflectionTelemetry
from mlos.intelligence.cache.llm_cache import LLMCache
from mlos.intelligence.config import ProviderConfig
from mlos.intelligence.intelligence_service import IntelligenceService
from mlos.intelligence.providers.mock_provider import MockProvider
from mlos.intelligence.schemas.reflection_output import (
    LLMObservation,
    LLMRecommendation,
    LLMReflectionOutput,
    LLMTrend,
)
from mlos.reflection.algorithms.hybrid_reflection_algorithm import (
    HybridReflectionAlgorithm,
)
from mlos.reflection.algorithms.llm_reflection_algorithm import LLMReflectionAlgorithm
from mlos.reflection.translator import ReflectionTranslator


@pytest.fixture(autouse=True)
def clean_mock_provider():
    LLMCache().clear()
    MockProvider.mock_responses.clear()
    MockProvider.mock_structured_responses.clear()
    yield
    LLMCache().clear()
    MockProvider.mock_responses.clear()
    MockProvider.mock_structured_responses.clear()


@pytest.fixture
def sample_reflection_context():
    eval_summary = EvaluationSummary(
        session_id="eval_001",
        metrics={"accuracy": 0.85, "loss": 0.15},
        checks={"accuracy_threshold": True},
    )
    exec_summary = ExecutionSummary(
        session_id="exec_001",
        status="SUCCESS",
        exit_code=0,
        duration_seconds=10.5,
        error_message=None,
    )
    plan_summary = PlanningSummary(
        session_id="plan_001",
        selected_strategy="RuleBasedPipeline",
        planned_steps=("impute", "scale", "train"),
    )
    rule = ActiveRuleSummary(
        subsystem="planning",
        component="validation_constraints",
        parameters={"allowed_scalers": "standard,minmax"},
    )

    return ReflectionContext(
        project_name="TestProj",
        project_goal="Accuracy",
        latest_planning=plan_summary,
        latest_execution=exec_summary,
        latest_evaluation=eval_summary,
        historical_plannings=(),
        historical_executions=(),
        historical_evaluations=(),
        knowledge_summary=KnowledgeSummary(rules=(rule,)),
    )


def test_reflection_telemetry_model():
    tel = ReflectionTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=10.5,
        cache_hit=False,
        fallback_used=False,
        validation_passed=True,
    )
    assert tel.provider == "mock"
    assert tel.model == "mock-gpt"
    assert tel.latency_ms == 10.5
    assert tel.cache_hit is False
    assert tel.fallback_used is False
    assert tel.validation_passed is True
    assert tel.request_id == ""
    assert tel.token_usage == {}
    assert tel.estimated_cost == 0.0


def test_prompt_variables_formatting(sample_reflection_context):
    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    variables = service._build_reflection_variables(sample_reflection_context)

    assert variables["project_name"] == "TestProj"
    assert "accuracy" in variables["metric_statistics"]
    assert "Success Rate: 100.0%" in variables["execution_statistics"]
    assert "RuleBasedPipeline" in variables["planning_statistics"]
    assert "Historical Runs Count" in variables["reflection_history"]
    assert "validation_constraints" in variables["knowledge_summary"]


def test_reflection_translator(sample_reflection_context):
    output = LLMReflectionOutput(
        summary="A stable training run.",
        insights=[
            LLMObservation(metric_key="accuracy", value=0.85, observed_at="eval_001")
        ],
        trends=[LLMTrend(metric_key="accuracy", direction="STABLE", slope=0.0)],
        recommendations=[
            LLMRecommendation(
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                action_type="ENABLE_IMPUTATION",
                parameters={"pipeline_type": "baseline"},
                priority="CRITICAL",
                reason="Accuracy is stable",
                expected_outcome="Establish baseline",
            )
        ],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="High confidence due to sufficient run logs.",
    )
    telemetry = ReflectionTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=1.5,
        cache_hit=False,
        fallback_used=False,
        validation_passed=True,
    )

    session = ReflectionTranslator.to_reflection_session(
        sample_reflection_context, output, telemetry
    )

    assert session.summary == "A stable training run."
    assert len(session.insights) == 2
    assert session.insights[0].insight_type == "OBSERVATION"
    assert session.insights[0].evidence == ("accuracy",)
    assert session.insights[1].insight_type == "METRIC_TREND"
    assert len(session.feedback) == 1
    assert session.feedback[0].priority == "CRITICAL"
    assert session.feedback[0].target_subsystem == "planning"
    assert session.confidence is not None
    assert session.confidence.accepted is True
    assert session.telemetry == telemetry


def test_llm_reflection_algorithm_success(sample_reflection_context):
    mock_output = LLMReflectionOutput(
        summary="LLM Reflected Successfully.",
        insights=[
            LLMObservation(metric_key="accuracy", value=0.85, observed_at="eval_001")
        ],
        trends=[LLMTrend(metric_key="accuracy", direction="STABLE", slope=0.0)],
        recommendations=[
            LLMRecommendation(
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                action_type="ENABLE_IMPUTATION",
                parameters={"pipeline_type": "baseline"},
                priority="CRITICAL",
                reason="Accuracy is stable",
                expected_outcome="Establish baseline",
            )
        ],
        confidence_score=0.95,
        uncertainty_score=0.05,
        explanation="Excellent score",
    )
    MockProvider.mock_structured_responses[LLMReflectionOutput] = mock_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = LLMReflectionAlgorithm(intelligence_service=service)

    session = algo.reflect(sample_reflection_context)

    assert session.summary == "LLM Reflected Successfully."
    assert session.telemetry is not None
    assert session.telemetry.provider == "mock"
    assert session.telemetry.model == "mock-gpt"
    assert session.telemetry.validation_passed is True
    assert session.telemetry.fallback_used is False


def test_llm_reflection_cache_behavior(sample_reflection_context):
    mock_output = LLMReflectionOutput(
        summary="LLM Reflected.",
        insights=[],
        trends=[],
        recommendations=[
            LLMRecommendation(
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                action_type="ENABLE_IMPUTATION",
                parameters={},
                priority="MEDIUM",
                reason="Reason",
                expected_outcome="Outcome",
            )
        ],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMReflectionOutput] = mock_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = LLMReflectionAlgorithm(intelligence_service=service)

    # First run (Cache Miss)
    session1 = algo.reflect(sample_reflection_context)
    assert session1.telemetry.cache_hit is False

    # Second run (Cache Hit)
    session2 = algo.reflect(sample_reflection_context)
    assert session2.telemetry.cache_hit is True


def test_hybrid_reflection_algorithm_success(sample_reflection_context):
    mock_output = LLMReflectionOutput(
        summary="Hybrid Success.",
        insights=[
            LLMObservation(metric_key="accuracy", value=0.85, observed_at="eval_001")
        ],
        trends=[LLMTrend(metric_key="accuracy", direction="STABLE", slope=0.0)],
        recommendations=[
            LLMRecommendation(
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                action_type="ENABLE_IMPUTATION",
                parameters={"pipeline_type": "baseline"},
                priority="CRITICAL",
                reason="None",
                expected_outcome="None",
            )
        ],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMReflectionOutput] = mock_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = HybridReflectionAlgorithm(intelligence_service=service)

    session = algo.reflect(sample_reflection_context)

    assert session.summary == "Hybrid Success."
    assert session.telemetry.validation_passed is True
    assert session.telemetry.fallback_used is False


def test_hybrid_reflection_validation_failures(sample_reflection_context):
    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = HybridReflectionAlgorithm(intelligence_service=service)

    # Scenario 1: Hallucinated metric names
    bad_output_hallucination = LLMReflectionOutput(
        summary="Hallucinated metric names output",
        insights=[
            LLMObservation(
                metric_key="hallucinated_metric", value=0.9, observed_at="eval_001"
            )
        ],
        trends=[],
        recommendations=[
            LLMRecommendation(
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                action_type="ENABLE_IMPUTATION",
                parameters={},
                priority="CRITICAL",
                reason="Reason",
                expected_outcome="Outcome",
            )
        ],
        confidence_score=0.8,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMReflectionOutput] = (
        bad_output_hallucination
    )

    session = algo.reflect(sample_reflection_context)
    # Rejects due to hallucination and falls back to rule-based summary
    assert "Reflection detected" in session.summary
    assert session.telemetry.validation_passed is False
    assert session.telemetry.fallback_used is True

    # Scenario 2: Invalid confidence score (>1.0)
    MockProvider.mock_structured_responses.clear()
    bad_output_confidence = LLMReflectionOutput(
        summary="Bad confidence output",
        insights=[],
        trends=[],
        recommendations=[
            LLMRecommendation(
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                action_type="ENABLE_IMPUTATION",
                parameters={},
                priority="CRITICAL",
                reason="Reason",
                expected_outcome="Outcome",
            )
        ],
        confidence_score=2.5,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMReflectionOutput] = bad_output_confidence

    session = algo.reflect(sample_reflection_context)
    assert session.telemetry.validation_passed is False
    assert session.telemetry.fallback_used is True

    # Scenario 3: Duplicate recommendations
    MockProvider.mock_structured_responses.clear()
    bad_output_duplicates = LLMReflectionOutput(
        summary="Duplicate recommendation output",
        insights=[],
        trends=[],
        recommendations=[
            LLMRecommendation(
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                action_type="ENABLE_IMPUTATION",
                parameters={},
                priority="CRITICAL",
                reason="Reason",
                expected_outcome="Outcome",
            ),
            LLMRecommendation(
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                action_type="ENABLE_IMPUTATION",
                parameters={},
                priority="CRITICAL",
                reason="Reason",
                expected_outcome="Outcome",
            ),
        ],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMReflectionOutput] = bad_output_duplicates

    session = algo.reflect(sample_reflection_context)
    assert session.telemetry.validation_passed is False
    assert session.telemetry.fallback_used is True


def test_hybrid_reflection_provider_exception_fallback(sample_reflection_context):
    mock_service = MagicMock(spec=IntelligenceService)
    mock_service.execute_subsystem.side_effect = RuntimeError("Service Unavailable")

    algo = HybridReflectionAlgorithm(intelligence_service=mock_service)
    session = algo.reflect(sample_reflection_context)

    # Should gracefully fall back to rule-based analysis
    assert "Reflection detected" in session.summary
    assert session.telemetry.validation_passed is False
    assert session.telemetry.fallback_used is True


def test_backward_compatibility():
    session = ReflectionSession(summary="Old Session", insights=[], feedback=[])
    assert session.telemetry is None


from mlos.cli.commands.reflect import ReflectCommand
from mlos.engine.engine import MLOSEngine
from mlos.reflection.algorithms.rule_based_reflection_algorithm import (
    RuleBasedReflectionAlgorithm,
)


@patch("mlos.cli.commands.reflect.find_project_root")
@patch("mlos.cli.commands.reflect.reconstruct_project_memory")
@patch("mlos.cli.commands.reflect.update_project_config_from_memory")
def test_cli_reflect_command_modes(
    mock_update, mock_reconstruct, mock_find_root, sample_reflection_context
):
    mock_find_root.return_value = Path("/dummy")
    from mlos.domain.models.project_memory import ProjectMemory

    memory = ProjectMemory(project_name="CliProj", project_goal="CliGoal")
    mock_reconstruct.return_value = memory

    engine = MLOSEngine()

    mock_session = MagicMock(spec=ReflectionSession)
    mock_session.summary = "CLI Reflection Session Output Summary"
    mock_session.insights = []
    mock_session.feedback = []
    mock_session.confidence = None
    mock_session.telemetry = ReflectionTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=1.2,
        cache_hit=False,
        fallback_used=False,
        validation_passed=True,
    )
    engine.reflect = MagicMock(return_value=mock_session)

    cmd = ReflectCommand()

    # Test --rule
    args = argparse.Namespace(rule=True, llm=False, hybrid=False)
    exit_code = cmd.handle(args, engine)
    assert exit_code == 0
    assert isinstance(
        engine.reflection_engine.reflection_algorithm, RuleBasedReflectionAlgorithm
    )

    # Test --llm
    args = argparse.Namespace(rule=False, llm=True, hybrid=False)
    exit_code = cmd.handle(args, engine)
    assert exit_code == 0
    assert isinstance(
        engine.reflection_engine.reflection_algorithm, LLMReflectionAlgorithm
    )

    # Test --hybrid
    args = argparse.Namespace(rule=False, llm=False, hybrid=True)
    exit_code = cmd.handle(args, engine)
    assert exit_code == 0
    assert isinstance(
        engine.reflection_engine.reflection_algorithm, HybridReflectionAlgorithm
    )
