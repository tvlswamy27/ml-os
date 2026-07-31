"""
Unit and integration tests for LLM Learning subsystem.

Author: Antigravity
License: MIT
"""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from mlos.domain.models.learning.learning_context import (
    LearningContext,
    ReflectionSummary,
    FeedbackSummary,
)
from mlos.domain.models.learning.learning_session import LearningSession
from mlos.domain.models.learning.learning_telemetry import LearningTelemetry
from mlos.domain.models.learning.learning_update_type import LearningUpdateType
from mlos.domain.models.knowledge_summary import KnowledgeSummary, ActiveRuleSummary
from mlos.intelligence.intelligence_service import IntelligenceService
from mlos.intelligence.config import ProviderConfig
from mlos.intelligence.providers.mock_provider import MockProvider
from mlos.intelligence.cache.llm_cache import LLMCache
from mlos.intelligence.schemas.learning_output import (
    LLMLearningOutput,
    LLMLearningPattern,
    LLMLearningProposal,
    LLMLearningEvidence,
)
from mlos.learning.translator import LearningTranslator
from mlos.learning.algorithms.llm_learning_algorithm import LLMLearningAlgorithm
from mlos.learning.algorithms.hybrid_learning_algorithm import (
    HybridLearningAlgorithm,
)
from mlos.planning.config import AlgorithmMode, get_planner_config


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
def sample_learning_context():
    fb_summary = FeedbackSummary(
        feedback_id="fb_001",
        target_subsystem="planning",
        target_component="HeuristicPlanningAlgorithm",
        action_type="ENABLE_IMPUTATION",
        parameters={"pipeline_type": "baseline"},
        priority="CRITICAL",
        reason="reason text",
    )
    ref_summary = ReflectionSummary(
        session_id="ref_001",
        summary="summary text",
        feedback=(fb_summary,),
        confidence_accepted=True,
    )
    rule = ActiveRuleSummary(
        subsystem="planning",
        component="validation_constraints",
        parameters={"allowed_scalers": "standard,minmax"},
    )

    return LearningContext(
        project_name="TestProj",
        project_goal="Accuracy",
        latest_reflection=ref_summary,
        historical_reflections=(),
        knowledge_summary=KnowledgeSummary(rules=(rule,)),
    )


def test_learning_telemetry_model():
    tel = LearningTelemetry(
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


def test_prompt_variables_formatting(sample_learning_context):
    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    variables = service._build_learning_variables(sample_learning_context)

    assert variables["project_name"] == "TestProj"
    assert "Latest Session ID: ref_001" in variables["reflection_summary"]
    assert "Total Feedback Count: 1" in variables["feedback_statistics"]
    assert "ENABLE_IMPUTATION" in variables["action_statistics"]
    assert "Stable Rate: 1.0000" in variables["trend_statistics"]
    assert "historical reflections" in variables["learning_history"]
    assert "validation_constraints" in variables["knowledge_summary"]


def test_learning_translator(sample_learning_context):
    evidence = LLMLearningEvidence(
        reflection_session_ids=["ref_001"],
        evaluation_session_ids=[],
        execution_session_ids=[],
        metrics_used=["accuracy"],
        confidence_values=[0.9],
        frequency_counts={"HeuristicPlanningAlgorithm": 1},
        trend_information={"accuracy": "stable"},
        supporting_observations=["obs text"],
    )
    output = LLMLearningOutput(
        summary="proposals generated",
        patterns=[
            LLMLearningPattern(
                pattern_id="pat_001",
                description="desc",
                frequency=1,
                is_failure_pattern=False,
            )
        ],
        proposals=[
            LLMLearningProposal(
                proposal_id="prop_001",
                update_type="ENABLE_GENERATOR",
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                parameters={"param": "value"},
                priority="CRITICAL",
                evidence=evidence,
            )
        ],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    telemetry = LearningTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=1.5,
        cache_hit=False,
        fallback_used=False,
        validation_passed=True,
    )

    session = LearningTranslator.to_learning_session(
        sample_learning_context, output, telemetry
    )

    assert session.summary == "proposals generated"
    assert len(session.updates) == 1
    assert session.updates[0].update_type == LearningUpdateType.ENABLE_GENERATOR
    assert session.updates[0].evidence.reflection_session_ids == ("ref_001",)
    assert isinstance(session.updates[0].evidence.reflection_session_ids, tuple)
    assert session.confidence is not None
    assert session.confidence.accepted is True
    assert session.telemetry == telemetry


def test_llm_learning_algorithm_success(sample_learning_context):
    evidence = LLMLearningEvidence(
        reflection_session_ids=["ref_001"],
        evaluation_session_ids=[],
        execution_session_ids=[],
        metrics_used=["accuracy"],
        confidence_values=[0.9],
        frequency_counts={"HeuristicPlanningAlgorithm": 1},
        trend_information={"accuracy": "stable"},
        supporting_observations=["obs text"],
    )
    mock_output = LLMLearningOutput(
        summary="LLM Learned Successfully.",
        patterns=[],
        proposals=[
            LLMLearningProposal(
                proposal_id="prop_001",
                update_type="ENABLE_GENERATOR",
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                parameters={"param": "value"},
                priority="CRITICAL",
                evidence=evidence,
            )
        ],
        confidence_score=0.95,
        uncertainty_score=0.05,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMLearningOutput] = mock_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = LLMLearningAlgorithm(intelligence_service=service)

    session = algo.learn(sample_learning_context)

    assert session.summary == "LLM Learned Successfully."
    assert session.telemetry is not None
    assert session.telemetry.provider == "mock"
    assert session.telemetry.validation_passed is True
    assert session.telemetry.fallback_used is False


def test_llm_learning_cache_behavior(sample_learning_context):
    evidence = LLMLearningEvidence(
        reflection_session_ids=["ref_001"],
        evaluation_session_ids=[],
        execution_session_ids=[],
        metrics_used=["accuracy"],
        confidence_values=[0.9],
        frequency_counts={"HeuristicPlanningAlgorithm": 1},
        trend_information={"accuracy": "stable"},
        supporting_observations=["obs text"],
    )
    mock_output = LLMLearningOutput(
        summary="LLM Learned.",
        patterns=[],
        proposals=[
            LLMLearningProposal(
                proposal_id="prop_001",
                update_type="ENABLE_GENERATOR",
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                parameters={},
                priority="MEDIUM",
                evidence=evidence,
            )
        ],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMLearningOutput] = mock_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = LLMLearningAlgorithm(intelligence_service=service)

    # First run (Cache Miss)
    session1 = algo.learn(sample_learning_context)
    assert session1.telemetry.cache_hit is False

    # Second run (Cache Hit)
    session2 = algo.learn(sample_learning_context)
    assert session2.telemetry.cache_hit is True


def test_hybrid_learning_algorithm_success(sample_learning_context):
    evidence = LLMLearningEvidence(
        reflection_session_ids=["ref_001"],
        evaluation_session_ids=[],
        execution_session_ids=[],
        metrics_used=["accuracy"],
        confidence_values=[0.9],
        frequency_counts={"HeuristicPlanningAlgorithm": 1},
        trend_information={"accuracy": "stable"},
        supporting_observations=["obs text"],
    )
    mock_output = LLMLearningOutput(
        summary="Hybrid Success.",
        patterns=[],
        proposals=[
            LLMLearningProposal(
                proposal_id="prop_001",
                update_type="ENABLE_GENERATOR",
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                parameters={"param": "value"},
                priority="CRITICAL",
                evidence=evidence,
            )
        ],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMLearningOutput] = mock_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = HybridLearningAlgorithm(intelligence_service=service)

    session = algo.learn(sample_learning_context)

    assert session.summary == "Hybrid Success."
    assert session.telemetry.validation_passed is True
    assert session.telemetry.fallback_used is False


def test_hybrid_learning_validation_failures(sample_learning_context):
    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = HybridLearningAlgorithm(intelligence_service=service)

    evidence = LLMLearningEvidence(
        reflection_session_ids=["ref_001"],
        evaluation_session_ids=[],
        execution_session_ids=[],
        metrics_used=["accuracy"],
        confidence_values=[0.9],
        frequency_counts={"HeuristicPlanningAlgorithm": 1},
        trend_information={"accuracy": "stable"},
        supporting_observations=["obs text"],
    )

    # Scenario 1: Hallucinated action target component (not in reflections history)
    bad_output_hallucination = LLMLearningOutput(
        summary="Hallucinated component output",
        patterns=[],
        proposals=[
            LLMLearningProposal(
                proposal_id="prop_001",
                update_type="ENABLE_GENERATOR",
                target_subsystem="planning",
                target_component="FictionalComponent",
                parameters={},
                priority="CRITICAL",
                evidence=evidence,
            )
        ],
        confidence_score=0.8,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMLearningOutput] = bad_output_hallucination

    session = algo.learn(sample_learning_context)
    assert session.telemetry.validation_passed is False
    assert session.telemetry.fallback_used is True

    # Scenario 2: Duplicate proposals
    MockProvider.mock_structured_responses.clear()
    bad_output_duplicates = LLMLearningOutput(
        summary="Duplicate proposals output",
        patterns=[],
        proposals=[
            LLMLearningProposal(
                proposal_id="prop_001",
                update_type="ENABLE_GENERATOR",
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                parameters={"param": "val"},
                priority="CRITICAL",
                evidence=evidence,
            ),
            LLMLearningProposal(
                proposal_id="prop_002",
                update_type="ENABLE_GENERATOR",
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                parameters={"param": "val"},
                priority="CRITICAL",
                evidence=evidence,
            ),
        ],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMLearningOutput] = bad_output_duplicates

    session = algo.learn(sample_learning_context)
    assert session.telemetry.validation_passed is False
    assert session.telemetry.fallback_used is True


def test_hybrid_learning_active_knowledge_rejection(sample_learning_context):
    evidence = LLMLearningEvidence(
        reflection_session_ids=["ref_001"],
        evaluation_session_ids=[],
        execution_session_ids=[],
        metrics_used=["accuracy"],
        confidence_values=[0.9],
        frequency_counts={"HeuristicPlanningAlgorithm": 1},
        trend_information={"accuracy": "stable"},
        supporting_observations=["obs text"],
    )
    # The active rule in context is subsystem='planning', component='validation_constraints', parameters={'allowed_scalers': 'standard,minmax'}
    # Let's propose an update that matches this active rule parameter signature
    mock_output = LLMLearningOutput(
        summary="Duplicate Active Rule proposed",
        patterns=[],
        proposals=[
            LLMLearningProposal(
                proposal_id="prop_001",
                update_type="ENABLE_GENERATOR",
                target_subsystem="planning",
                target_component="validation_constraints",
                parameters={"allowed_scalers": "standard,minmax"},
                priority="CRITICAL",
                evidence=evidence,
            )
        ],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMLearningOutput] = mock_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = HybridLearningAlgorithm(intelligence_service=service)

    session = algo.learn(sample_learning_context)
    # Rejects due to matching active knowledge and falls back
    assert session.telemetry.validation_passed is False
    assert session.telemetry.fallback_used is True


def test_hybrid_learning_provider_exception_fallback(sample_learning_context):
    mock_service = MagicMock(spec=IntelligenceService)
    mock_service.execute_subsystem.side_effect = RuntimeError("Service Unavailable")

    algo = HybridLearningAlgorithm(intelligence_service=mock_service)
    session = algo.learn(sample_learning_context)

    # Should gracefully fall back
    assert session.telemetry.validation_passed is False
    assert session.telemetry.fallback_used is True


def test_backward_compatibility():
    session = LearningSession(summary="Old Session", updates=[])
    assert session.telemetry is None


from mlos.cli.commands.learn import LearnCommand
from mlos.engine.engine import MLOSEngine
from mlos.learning.algorithms.rule_based_learning_algorithm import (
    RuleBasedLearningAlgorithm,
)


@patch("mlos.cli.commands.learn.find_project_root")
@patch("mlos.cli.commands.learn.reconstruct_project_memory")
@patch("mlos.cli.commands.learn.update_project_config_from_memory")
def test_cli_learn_command_modes(
    mock_update, mock_reconstruct, mock_find_root, sample_learning_context
):
    mock_find_root.return_value = Path("/dummy")
    from mlos.domain.models.project_memory import ProjectMemory

    memory = ProjectMemory(project_name="CliProj", project_goal="CliGoal")
    mock_reconstruct.return_value = memory

    engine = MLOSEngine()

    mock_session = MagicMock(spec=LearningSession)
    mock_session.summary = "CLI Learning Session Output Summary"
    mock_session.updates = []
    mock_session.confidence = None
    mock_session.telemetry = LearningTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=1.2,
        cache_hit=False,
        fallback_used=False,
        validation_passed=True,
    )
    engine.learn = MagicMock(return_value=mock_session)

    cmd = LearnCommand()

    # Test --rule
    args = argparse.Namespace(rule=True, llm=False, hybrid=False)
    exit_code = cmd.handle(args, engine)
    assert exit_code == 0
    assert isinstance(
        engine.learning_engine.learning_algorithm, RuleBasedLearningAlgorithm
    )

    # Test --llm
    args = argparse.Namespace(rule=False, llm=True, hybrid=False)
    exit_code = cmd.handle(args, engine)
    assert exit_code == 0
    assert isinstance(engine.learning_engine.learning_algorithm, LLMLearningAlgorithm)

    # Test --hybrid
    args = argparse.Namespace(rule=False, llm=False, hybrid=True)
    exit_code = cmd.handle(args, engine)
    assert exit_code == 0
    assert isinstance(
        engine.learning_engine.learning_algorithm, HybridLearningAlgorithm
    )
