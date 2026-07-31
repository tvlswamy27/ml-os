"""
Unit and integration tests for the LLM Knowledge subsystem.

Author: Antigravity
License: MIT
"""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from datetime import datetime

from mlos.domain.models.knowledge.knowledge_context import (
    KnowledgeContext,
    LearningSummary,
    LearningUpdateSummary,
    KnowledgeSummary,
)
from mlos.domain.models.knowledge.knowledge_entry import KnowledgeEntry
from mlos.domain.models.knowledge.knowledge_entry_type import KnowledgeEntryType
from mlos.domain.models.knowledge.knowledge_status import KnowledgeStatus
from mlos.domain.models.knowledge.knowledge_version import KnowledgeVersion
from mlos.domain.models.knowledge.knowledge_confidence import KnowledgeConfidence
from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession
from mlos.domain.models.knowledge.knowledge_promotion_decision import (
    KnowledgePromotionType,
    KnowledgeImpact,
    KnowledgePromotionDecision,
)
from mlos.domain.models.knowledge.knowledge_telemetry import KnowledgeTelemetry
from mlos.intelligence.intelligence_service import IntelligenceService
from mlos.intelligence.config import ProviderConfig
from mlos.intelligence.providers.mock_provider import MockProvider
from mlos.intelligence.cache.llm_cache import LLMCache
from mlos.intelligence.schemas.knowledge_output import (
    LLMKnowledgeOutput,
    LLMKnowledgePromotion,
    LLMKnowledgeConflict,
    LLMKnowledgeImpact,
)
from mlos.knowledge.translator import KnowledgeTranslator
from mlos.knowledge.algorithms.llm_knowledge_algorithm import (
    LLMKnowledgeAlgorithm,
)
from mlos.knowledge.algorithms.hybrid_knowledge_algorithm import (
    HybridKnowledgeAlgorithm,
)


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
def sample_knowledge_context():
    up_summary = LearningUpdateSummary(
        update_id="up_001",
        update_type="ENABLE_GENERATOR",
        target_subsystem="planning",
        target_component="HeuristicPlanningAlgorithm",
        parameters={"pipeline_type": "baseline"},
        confidence_score=0.9,
        evidence_observations=("obs text",),
    )
    ls_summary = LearningSummary(
        session_id="learn_001",
        updates=(up_summary,),
        confidence_accepted=True,
    )
    existing_entry = KnowledgeEntry(
        knowledge_id="old_001",
        knowledge_type=KnowledgeEntryType.PARAMETER_PRIOR,
        target_subsystem="planning",
        target_component="HeuristicPlanningAlgorithm",
        parameters={"pipeline_type": "baseline"},
        source_learning_sessions=("learn_prev",),
        evidence_summary="previous evidence",
        version=KnowledgeVersion(
            version_number=1,
            parent_entry_id=None,
            timestamp=datetime.now(),
            change_summary="Initial version",
            reason="Baseline configuration",
        ),
        created_at=datetime.now(),
        last_used=None,
        usage_count=0,
        confidence=KnowledgeConfidence(
            score=0.8,
            uncertainty=0.2,
            support_count=1,
            usage_history_count=0,
            explanation="Initial run details",
        ),
        status=KnowledgeStatus.ACTIVE,
    )

    return KnowledgeContext(
        project_name="TestProj",
        project_goal="Accuracy",
        latest_learning=ls_summary,
        historical_learnings=(),
        existing_knowledge=KnowledgeSummary(active_entries=(existing_entry,)),
    )


def test_knowledge_telemetry_model():
    tel = KnowledgeTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=12.4,
        cache_hit=True,
        fallback_used=False,
        validation_passed=True,
    )
    assert tel.provider == "mock"
    assert tel.model == "mock-gpt"
    assert tel.latency_ms == 12.4
    assert tel.cache_hit is True
    assert tel.fallback_used is False
    assert tel.validation_passed is True


def test_prompt_variables_formatting(sample_knowledge_context):
    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    variables = service._build_knowledge_variables(sample_knowledge_context)

    assert variables["project_name"] == "TestProj"
    assert "learn_001" in variables["learning_summary"]
    assert "ENABLE_GENERATOR" in variables["proposal_statistics"]
    assert "Total Active Policies: 1" in variables["active_policy_statistics"]
    assert "HeuristicPlanningAlgorithm" in variables["active_knowledge"]


def test_knowledge_translator(sample_knowledge_context):
    mock_impact = LLMKnowledgeImpact(
        expected_accuracy_delta=0.05,
        expected_latency_delta=-10.0,
        expected_memory_delta=0.0,
        expected_stability_delta=0.1,
        expected_explainability_delta=0.0,
    )
    mock_promotion = LLMKnowledgePromotion(
        decision_type="PROMOTE_ACTIVE",
        target_entry_id="old_001",
        target_component="HeuristicPlanningAlgorithm",
        target_subsystem="planning",
        promotion_reason="Improved metrics",
        confidence=0.9,
        evidence=["learn_001"],
        expected_impact=mock_impact,
    )
    mock_conflict = LLMKnowledgeConflict(
        conflict_id="con_001",
        subsystem="planning",
        component="HeuristicPlanningAlgorithm",
        parameter_name="pipeline_type",
        competing_values=["baseline", "advanced"],
        resolution_applied="baseline",
    )
    mock_output = LLMKnowledgeOutput(
        summary="Promotion summary details",
        promotions=[mock_promotion],
        conflicts=[mock_conflict],
        confidence_score=0.95,
        uncertainty_score=0.05,
        explanation="Explain",
    )
    telemetry = KnowledgeTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=1.5,
        cache_hit=False,
        fallback_used=False,
        validation_passed=True,
    )

    decisions = KnowledgeTranslator.to_promotion_decisions(mock_output)
    conflicts = KnowledgeTranslator.to_conflicts(mock_output)
    session = KnowledgeTranslator.to_knowledge_session(
        sample_knowledge_context, mock_output, telemetry
    )

    assert len(decisions) == 1
    assert decisions[0].decision_type == KnowledgePromotionType.PROMOTE_ACTIVE
    assert decisions[0].expected_impact.expected_accuracy_delta == 0.05
    assert isinstance(decisions[0].evidence, tuple)
    assert len(conflicts) == 1
    assert conflicts[0].resolution_applied == "baseline"
    assert session.telemetry == telemetry


def test_llm_knowledge_algorithm_success(sample_knowledge_context):
    mock_impact = LLMKnowledgeImpact(
        expected_accuracy_delta=0.05,
        expected_latency_delta=-10.0,
    )
    mock_output = LLMKnowledgeOutput(
        summary="LLM Promoted Successfully.",
        promotions=[
            LLMKnowledgePromotion(
                decision_type="PROMOTE_ACTIVE",
                target_entry_id="old_001",
                target_component="HeuristicPlanningAlgorithm",
                target_subsystem="planning",
                promotion_reason="Reason",
                confidence=0.9,
                evidence=["up_001"],
                expected_impact=mock_impact,
            )
        ],
        conflicts=[],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMKnowledgeOutput] = mock_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = LLMKnowledgeAlgorithm(intelligence_service=service)

    session = algo.manage(sample_knowledge_context)

    assert session.summary == "LLM Promoted Successfully."
    assert len(session.promoted_entries) == 1
    assert session.promoted_entries[0].version.version_number == 2
    assert session.promoted_entries[0].version.parent_entry_id == "old_001"
    assert session.telemetry.validation_passed is True


def test_llm_knowledge_cache_behavior(sample_knowledge_context):
    mock_impact = LLMKnowledgeImpact()
    mock_output = LLMKnowledgeOutput(
        summary="LLM Promoted.",
        promotions=[
            LLMKnowledgePromotion(
                decision_type="PROMOTE_ACTIVE",
                target_entry_id="old_001",
                target_component="HeuristicPlanningAlgorithm",
                target_subsystem="planning",
                promotion_reason="Reason",
                confidence=0.9,
                evidence=["up_001"],
                expected_impact=mock_impact,
            )
        ],
        conflicts=[],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMKnowledgeOutput] = mock_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = LLMKnowledgeAlgorithm(intelligence_service=service)

    # First run (Cache Miss)
    session1 = algo.manage(sample_knowledge_context)
    assert session1.telemetry.cache_hit is False

    # Second run (Cache Hit)
    session2 = algo.manage(sample_knowledge_context)
    assert session2.telemetry.cache_hit is True


def test_hybrid_knowledge_algorithm_success(sample_knowledge_context):
    mock_impact = LLMKnowledgeImpact()
    mock_output = LLMKnowledgeOutput(
        summary="Hybrid Success.",
        promotions=[
            LLMKnowledgePromotion(
                decision_type="PROMOTE_ACTIVE",
                target_entry_id="old_001",
                target_component="HeuristicPlanningAlgorithm",
                target_subsystem="planning",
                promotion_reason="Reason",
                confidence=0.9,
                evidence=["up_001"],
                expected_impact=mock_impact,
            )
        ],
        conflicts=[],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMKnowledgeOutput] = mock_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = HybridKnowledgeAlgorithm(intelligence_service=service)

    session = algo.manage(sample_knowledge_context)

    assert session.summary == "Hybrid Success."
    assert session.telemetry.validation_passed is True
    assert session.telemetry.fallback_used is False


def test_hybrid_knowledge_validation_failures(sample_knowledge_context):
    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = HybridKnowledgeAlgorithm(intelligence_service=service)

    mock_impact = LLMKnowledgeImpact()

    # Scenario 1: Hallucinated component target (not in incoming updates or active policies)
    bad_output_hallucination = LLMKnowledgeOutput(
        summary="Hallucinated component output",
        promotions=[
            LLMKnowledgePromotion(
                decision_type="PROMOTE_ACTIVE",
                target_entry_id=None,
                target_component="FictionalComponent",
                target_subsystem="planning",
                promotion_reason="Reason",
                confidence=0.9,
                evidence=["up_001"],
                expected_impact=mock_impact,
            )
        ],
        conflicts=[],
        confidence_score=0.8,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMKnowledgeOutput] = (
        bad_output_hallucination
    )

    session = algo.manage(sample_knowledge_context)
    assert session.telemetry.validation_passed is False
    assert session.telemetry.fallback_used is True

    # Scenario 2: Promotion without accepted learning confidence
    MockProvider.mock_structured_responses.clear()
    unaccepted_learning_context = KnowledgeContext(
        project_name="TestProj",
        project_goal="Accuracy",
        latest_learning=LearningSummary(
            session_id="learn_002",
            updates=(
                LearningUpdateSummary(
                    update_id="up_002",
                    update_type="ENABLE_GENERATOR",
                    target_subsystem="planning",
                    target_component="HeuristicPlanningAlgorithm",
                    parameters={"pipeline_type": "baseline"},
                    confidence_score=0.4,
                    evidence_observations=(),
                ),
            ),
            confidence_accepted=False,  # Rejection key
        ),
        historical_learnings=(),
        existing_knowledge=sample_knowledge_context.existing_knowledge,
    )
    mock_unaccepted_output = LLMKnowledgeOutput(
        summary="Unaccepted Learning update promotion",
        promotions=[
            LLMKnowledgePromotion(
                decision_type="PROMOTE_ACTIVE",
                target_entry_id="old_001",
                target_component="HeuristicPlanningAlgorithm",
                target_subsystem="planning",
                promotion_reason="Reason",
                confidence=0.9,
                evidence=["up_002"],
                expected_impact=mock_impact,
            )
        ],
        conflicts=[],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMKnowledgeOutput] = mock_unaccepted_output

    session = algo.manage(unaccepted_learning_context)
    assert session.telemetry.validation_passed is False
    assert session.telemetry.fallback_used is True


def test_hybrid_knowledge_deprecated_parent_rejection(sample_knowledge_context):
    mock_impact = LLMKnowledgeImpact()
    # Add a deprecated parent entry
    deprecated_entry = KnowledgeEntry(
        knowledge_id="dep_001",
        knowledge_type=KnowledgeEntryType.PARAMETER_PRIOR,
        target_subsystem="planning",
        target_component="HeuristicPlanningAlgorithm",
        parameters={"pipeline_type": "baseline"},
        source_learning_sessions=(),
        evidence_summary="deprecated",
        version=KnowledgeVersion(
            version_number=1,
            parent_entry_id=None,
            timestamp=datetime.now(),
            change_summary="",
            reason="",
        ),
        created_at=datetime.now(),
        last_used=None,
        usage_count=0,
        confidence=KnowledgeConfidence(
            score=0.5,
            uncertainty=0.5,
            support_count=0,
            usage_history_count=0,
            explanation="",
        ),
        status=KnowledgeStatus.DEPRECATED,  # Deprecated key
    )
    context_with_deprecated = KnowledgeContext(
        project_name="TestProj",
        project_goal="Accuracy",
        latest_learning=sample_knowledge_context.latest_learning,
        historical_learnings=(),
        existing_knowledge=KnowledgeSummary(active_entries=(deprecated_entry,)),
    )
    mock_output = LLMKnowledgeOutput(
        summary="Deprecated parent promotion",
        promotions=[
            LLMKnowledgePromotion(
                decision_type="PROMOTE_ACTIVE",
                target_entry_id="dep_001",
                target_component="HeuristicPlanningAlgorithm",
                target_subsystem="planning",
                promotion_reason="Reason",
                confidence=0.9,
                evidence=["up_001"],
                expected_impact=mock_impact,
            )
        ],
        conflicts=[],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMKnowledgeOutput] = mock_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = HybridKnowledgeAlgorithm(intelligence_service=service)

    session = algo.manage(context_with_deprecated)
    assert session.telemetry.validation_passed is False
    assert session.telemetry.fallback_used is True


def test_backward_compatibility():
    session = KnowledgeSession(summary="Old Session", promoted_entries=[])
    assert session.telemetry is None


from mlos.cli.commands.knowledge import KnowledgeCommand
from mlos.engine.engine import MLOSEngine
from mlos.knowledge.algorithms.rule_based_knowledge_algorithm import (
    RuleBasedKnowledgeAlgorithm,
)


@patch("mlos.cli.commands.knowledge.find_project_root")
@patch("mlos.cli.commands.knowledge.reconstruct_project_memory")
@patch("mlos.cli.commands.knowledge.update_project_config_from_memory")
def test_cli_knowledge_command_modes(
    mock_update, mock_reconstruct, mock_find_root, sample_knowledge_context
):
    mock_find_root.return_value = Path("/dummy")
    from mlos.domain.models.project_memory import ProjectMemory

    memory = ProjectMemory(project_name="CliProj", project_goal="CliGoal")
    mock_reconstruct.return_value = memory

    engine = MLOSEngine()

    mock_session = MagicMock(spec=KnowledgeSession)
    mock_session.summary = "CLI Knowledge Session Output Summary"
    mock_session.promoted_entries = []
    mock_session.conflicts = []
    mock_session.telemetry = KnowledgeTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=1.2,
        cache_hit=False,
        fallback_used=False,
        validation_passed=True,
    )
    engine.manage_knowledge = MagicMock(return_value=mock_session)

    cmd = KnowledgeCommand()

    # Test --rule
    args = argparse.Namespace(rule=True, llm=False, hybrid=False)
    exit_code = cmd.handle(args, engine)
    assert exit_code == 0
    assert isinstance(
        engine.knowledge_engine.knowledge_algorithm, RuleBasedKnowledgeAlgorithm
    )

    # Test --llm
    args = argparse.Namespace(rule=False, llm=True, hybrid=False)
    exit_code = cmd.handle(args, engine)
    assert exit_code == 0
    assert isinstance(
        engine.knowledge_engine.knowledge_algorithm, LLMKnowledgeAlgorithm
    )

    # Test --hybrid
    args = argparse.Namespace(rule=False, llm=False, hybrid=True)
    exit_code = cmd.handle(args, engine)
    assert exit_code == 0
    assert isinstance(
        engine.knowledge_engine.knowledge_algorithm, HybridKnowledgeAlgorithm
    )
