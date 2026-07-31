"""
End-to-End integration, benchmark, and plugin manager hardening tests.

Author: Antigravity
License: MIT
"""

import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest
from datetime import datetime

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.run_context import RunContext
from mlos.domain.models.planning.planning_telemetry import PlanningTelemetry
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.planning.planning_context import PlanningContext
from mlos.domain.models.reflection.reflection_session import ReflectionSession
from mlos.domain.models.reflection.reflection_telemetry import ReflectionTelemetry
from mlos.domain.models.learning.learning_session import LearningSession
from mlos.domain.models.learning.learning_telemetry import LearningTelemetry
from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession
from mlos.domain.models.knowledge.knowledge_telemetry import KnowledgeTelemetry
from mlos.observability.telemetry import TelemetryAggregator
from mlos.plugins.manager import PluginRegistry, PluginType
from mlos.benchmark.framework import BenchmarkRunner
from mlos.engine.engine import MLOSEngine
from mlos.intelligence.providers.mock_provider import MockProvider
from mlos.intelligence.cache.llm_cache import LLMCache
from mlos.intelligence.schemas.planning_output import LLMPlanningOutput
from mlos.intelligence.schemas.reflection_output import LLMReflectionOutput
from mlos.intelligence.schemas.learning_output import LLMLearningOutput
from mlos.intelligence.schemas.knowledge_output import LLMKnowledgeOutput


@pytest.fixture(autouse=True)
def clean_mock_provider():
    LLMCache().clear()
    MockProvider.mock_responses.clear()
    MockProvider.mock_structured_responses.clear()
    PluginRegistry().clear()
    yield
    LLMCache().clear()
    MockProvider.mock_responses.clear()
    MockProvider.mock_structured_responses.clear()
    PluginRegistry().clear()


def test_run_context_telemetry_reference():
    rc = RunContext(
        run_id="run_001",
        iteration_id=1,
        project_id="proj_001",
        mode="hybrid",
        provider="mock",
        model="mock-gpt",
        start_time=datetime.now(),
    )
    tel = PlanningTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=10.0,
        cache_hit=False,
        fallback_used=False,
        validation_passed=True,
        run_context=rc,
    )
    assert tel.run_context == rc
    assert tel.run_context.iteration_id == 1


def test_plugin_registry_manifest_validation(tmp_path):
    registry = PluginRegistry()

    # 1. Compatible plugin
    compatible_code = """
PLUGIN_INFO = {
    "name": "MockPlannerPlugin",
    "version": "1.0.0",
    "type": "PLANNING",
    "author": "Core Team",
    "mlos_version": "2.1.0",
    "entry_point": "MockPlannerClass"
}

class MockPlannerClass:
    pass
"""
    plugin_file = tmp_path / "mock_plugin.py"
    plugin_file.write_text(compatible_code)

    registered = registry.register_plugin(plugin_file)
    assert registered is True
    assert (
        registry.get_plugin_class(PluginType.PLANNING, "MockPlannerPlugin") is not None
    )

    # 2. Incompatible plugin (bad version)
    incompatible_code = """
PLUGIN_INFO = {
    "name": "BadPlannerPlugin",
    "version": "1.0.0",
    "type": "PLANNING",
    "author": "Core Team",
    "mlos_version": "1.0.0",
    "entry_point": "BadPlannerClass"
}

class BadPlannerClass:
    pass
"""
    bad_plugin_file = tmp_path / "bad_plugin.py"
    bad_plugin_file.write_text(incompatible_code)

    registered_bad = registry.register_plugin(bad_plugin_file)
    assert registered_bad is False


def test_telemetry_aggregator_timeline():
    memory = ProjectMemory(
        project_name="TelemetryProj", project_goal="Verify timelines"
    )
    rc = RunContext(
        run_id="run_001",
        iteration_id=1,
        project_id="proj_001",
        mode="hybrid",
        provider="mock",
        model="mock-gpt",
        start_time=datetime.now(),
    )

    # Mock sessions
    p_tel = PlanningTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=500.0,
        cache_hit=False,
        fallback_used=False,
        validation_passed=True,
        run_context=rc,
    )
    p_session = PlanningSession(
        context=PlanningContext(project_name="TelemetryProj", goals=()),
        status="SUCCESS",
        telemetry=p_tel,
    )
    memory.planning_sessions.append(p_session)

    r_tel = ReflectionTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=300.0,
        cache_hit=True,
        fallback_used=False,
        validation_passed=True,
        run_context=rc,
    )
    memory.reflection_sessions.append(
        ReflectionSession(summary="Reflected.", telemetry=r_tel)
    )

    l_tel = LearningTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=100.0,
        cache_hit=False,
        fallback_used=True,
        validation_passed=False,
        run_context=rc,
    )
    memory.learning_sessions.append(
        LearningSession(summary="Learned.", telemetry=l_tel)
    )

    k_tel = KnowledgeTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=200.0,
        cache_hit=True,
        fallback_used=False,
        validation_passed=True,
        run_context=rc,
    )
    memory.knowledge_sessions.append(
        KnowledgeSession(summary="Knowledge managed.", telemetry=k_tel)
    )

    timeline = TelemetryAggregator.compile_timeline(memory)
    summary = TelemetryAggregator.get_summary(memory)

    assert len(timeline) == 4
    assert summary["total_tokens"] == 0
    assert summary["subsystems"]["planning"]["count"] == 1
    assert summary["subsystems"]["learning"]["fallback_frequency"] == 1.0
    assert summary["subsystems"]["reflection"]["cache_hit_rate"] == 1.0


def test_benchmark_runner_and_save_outputs(tmp_path):
    # Setup structured LLM outputs to prevent exceptions in test benchmark run
    from mlos.intelligence.schemas.planning_output import LLMPlanningOutput
    from mlos.intelligence.schemas.reflection_output import LLMReflectionOutput
    from mlos.intelligence.schemas.learning_output import LLMLearningOutput
    from mlos.intelligence.schemas.knowledge_output import LLMKnowledgeOutput

    MockProvider.mock_structured_responses[LLMPlanningOutput] = LLMPlanningOutput(
        strategy_name="BaselineStrategy",
        strategy_description="Select baseline",
        topological_steps=[],
        parameters={},
        confidence=0.9,
        reasoning="reasoning text",
        alternative_candidates=[],
        constraints=[],
    )

    MockProvider.mock_structured_responses[LLMReflectionOutput] = LLMReflectionOutput(
        summary="Reflected successfully.",
        observations=[],
        trends=[],
        feedback=[],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMLearningOutput] = LLMLearningOutput(
        summary="Learned successfully.",
        patterns=[],
        proposals=[],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMKnowledgeOutput] = LLMKnowledgeOutput(
        summary="Knowledge updated.",
        promotions=[],
        conflicts=[],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )

    runner = BenchmarkRunner(["playground/sample.csv"])
    results = runner.run_benchmark()

    assert len(results) == 3  # RULE, LLM, HYBRID
    assert results[0]["dataset"] == "sample.csv"

    runner.save_outputs(tmp_path)
    assert (tmp_path / "run.json").exists()
    assert (tmp_path / "run.csv").exists()
    assert (tmp_path / "summary.md").exists()


def test_long_running_adaptation_integration():
    # Execute multiple complete loop cycles, verifying evolving knowledge adaptation:
    # Iteration 1 -> Knowledge Update -> Iteration 2 -> Knowledge Update -> Iteration 3
    from mlos.intelligence.schemas.planning_output import LLMPlanningOutput
    from mlos.intelligence.schemas.reflection_output import (
        LLMReflectionOutput,
        LLMRecommendation,
    )
    from mlos.intelligence.schemas.learning_output import (
        LLMLearningOutput,
        LLMLearningProposal,
        LLMLearningEvidence,
    )
    from mlos.intelligence.schemas.knowledge_output import (
        LLMKnowledgeOutput,
        LLMKnowledgePromotion,
        LLMKnowledgeImpact,
    )

    # Step 1: Pre-populate LLM structured responses
    MockProvider.mock_structured_responses[LLMPlanningOutput] = LLMPlanningOutput(
        strategy_name="BaselineStrategy",
        strategy_description="Select baseline",
        topological_steps=[],
        parameters={},
        confidence=0.9,
        reasoning="reasoning text",
        alternative_candidates=[],
        constraints=[],
    )
    MockProvider.mock_structured_responses[LLMReflectionOutput] = LLMReflectionOutput(
        summary="Reflected successfully.",
        insights=[],
        trends=[],
        recommendations=[
            LLMRecommendation(
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                action_type="ENABLE_IMPUTATION",
                parameters={"allowed_scalers": "standard"},
                priority="CRITICAL",
                reason="Improve accuracy",
                expected_outcome="Improved metrics",
            )
        ],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMLearningOutput] = LLMLearningOutput(
        summary="Learned successfully.",
        patterns=[],
        proposals=[
            LLMLearningProposal(
                proposal_id="prop_001",
                update_type="ENABLE_GENERATOR",
                target_subsystem="planning",
                target_component="HeuristicPlanningAlgorithm",
                parameters={"allowed_scalers": "standard"},
                priority="CRITICAL",
                evidence=LLMLearningEvidence(
                    reflection_session_ids=["ref_001"],
                    evaluation_session_ids=[],
                    execution_session_ids=[],
                ),
            )
        ],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )
    MockProvider.mock_structured_responses[LLMKnowledgeOutput] = LLMKnowledgeOutput(
        summary="Knowledge updated.",
        promotions=[
            LLMKnowledgePromotion(
                decision_type="PROMOTE_ACTIVE",
                target_entry_id=None,
                target_component="HeuristicPlanningAlgorithm",
                target_subsystem="planning",
                promotion_reason="Improved metrics",
                confidence=0.95,
                evidence=["prop_001"],
                expected_impact=LLMKnowledgeImpact(expected_accuracy_delta=0.05),
            )
        ],
        conflicts=[],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )

    # Initialize hybrid cognitive loop engine
    engine = MLOSEngine()
    engine.create_project(name="AdaptProj", goal="Verify Evolving Knowledge")

    # Set mode to HYBRID across planning, reflection, learning, knowledge
    from mlos.planning.algorithms.hybrid_planning_algorithm import (
        HybridPlanningAlgorithm,
    )
    from mlos.reflection.algorithms.hybrid_reflection_algorithm import (
        HybridReflectionAlgorithm,
    )
    from mlos.learning.algorithms.hybrid_learning_algorithm import (
        HybridLearningAlgorithm,
    )
    from mlos.knowledge.algorithms.hybrid_knowledge_algorithm import (
        HybridKnowledgeAlgorithm,
    )

    engine.planning_engine.planning_algorithm = HybridPlanningAlgorithm()
    engine.reflection_engine.reflection_algorithm = HybridReflectionAlgorithm()
    engine.learning_engine.learning_algorithm = HybridLearningAlgorithm()
    engine.knowledge_engine.knowledge_algorithm = HybridKnowledgeAlgorithm()

    # Iteration 1
    engine.analyze("playground/sample.csv")
    engine.plan()
    engine.decide()
    engine.generate()
    engine.assemble()
    engine.execute()
    engine.evaluate()
    engine.reflect()
    engine.learn()
    session1 = engine.manage_knowledge()

    assert len(session1.promoted_entries) == 1
    assert session1.promoted_entries[0].version.version_number == 1

    # Iteration 2
    # Configure mock prompts to simulate the second iteration promoting version 2 of the rule
    MockProvider.mock_structured_responses[LLMKnowledgeOutput] = LLMKnowledgeOutput(
        summary="Knowledge updated version 2.",
        promotions=[
            LLMKnowledgePromotion(
                decision_type="PROMOTE_ACTIVE",
                target_entry_id=session1.promoted_entries[0].knowledge_id,
                target_component="HeuristicPlanningAlgorithm",
                target_subsystem="planning",
                promotion_reason="Improved metrics even more",
                confidence=0.98,
                evidence=["prop_002"],
                expected_impact=LLMKnowledgeImpact(expected_accuracy_delta=0.02),
            )
        ],
        conflicts=[],
        confidence_score=0.9,
        uncertainty_score=0.1,
        explanation="Explain",
    )

    engine.analyze("playground/sample.csv")
    engine.plan()
    engine.decide()
    engine.generate()
    engine.assemble()
    engine.execute()
    engine.evaluate()
    engine.reflect()
    engine.learn()
    session2 = engine.manage_knowledge()

    # Evolving version lineage correctly tracked
    v2_entries = [e for e in session2.promoted_entries if e.version.version_number == 2]
    assert len(v2_entries) == 1
    assert v2_entries[0].version.parent_entry_id == session1.promoted_entries[0].knowledge_id

