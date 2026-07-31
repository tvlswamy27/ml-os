"""
Comprehensive tests for LLM planning algorithms and structures.
"""

import os
import shutil
import pytest
from unittest.mock import MagicMock

from mlos.planning.config import AlgorithmMode, get_planner_config
from mlos.planning.algorithms.llm_planning_algorithm import LLMPlanningAlgorithm
from mlos.planning.algorithms.hybrid_planning_algorithm import (
    HybridPlanningAlgorithm,
    DEFAULT_VALIDATION_CONSTRAINTS,
)
from mlos.planning.translator import PlanningTranslator
from mlos.domain.models.planning.planning_context import PlanningContext
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.planning.planning_telemetry import PlanningTelemetry
from mlos.domain.models.planning.observation import Observation
from mlos.domain.models.planning.goal import Goal
from mlos.domain.models.knowledge_summary import KnowledgeSummary, ActiveRuleSummary
from mlos.intelligence.config import ProviderConfig
from mlos.intelligence.intelligence_service import IntelligenceService
from mlos.intelligence.providers.mock_provider import MockProvider
from mlos.intelligence.schemas.planning_output import (
    LLMPlanningOutput,
    LLMCandidateStrategy,
)
from mlos.intelligence.cache.llm_cache import LLMCache
from mlos.intelligence.prompts.prompt_manager import PromptManager


@pytest.fixture
def mock_planning_output():
    return LLMPlanningOutput(
        strategy_name="LLMPipeline",
        strategy_description="Advanced LLM-generated pipeline",
        topological_steps=["impute", "scale", "train"],
        parameters={"imputer": "median", "scaler": "minmax", "test_size": "0.2"},
        confidence=0.9,
        reasoning="Highly recommended for this layout",
        alternative_candidates=[
            LLMCandidateStrategy(
                strategy_name="AlternativePipe",
                description="Alternative baseline",
                steps=["impute", "train"],
            )
        ],
        constraints=["none"],
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
def temp_cache_dir():
    path = ".gemini/test_planning_cache"
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)
    yield path
    if os.path.exists(path):
        shutil.rmtree(path)


def test_algorithm_mode_enum():
    assert AlgorithmMode.RULE.value == "rule"
    assert AlgorithmMode.LLM.value == "llm"
    assert AlgorithmMode.HYBRID.value == "hybrid"


def test_planning_telemetry_model():
    telemetry = PlanningTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=15.0,
        cache_hit=False,
        fallback_used=True,
        validation_passed=False,
        request_id="req-123",
        token_usage={"total_tokens": 100},
        estimated_cost=0.005,
    )
    assert telemetry.provider == "mock"
    assert telemetry.latency_ms == 15.0
    assert telemetry.fallback_used is True
    assert telemetry.validation_passed is False
    assert telemetry.token_usage == {"total_tokens": 100}
    assert telemetry.estimated_cost == 0.005


def test_prompt_variables_loader_and_formatting():
    # Verify default prompt loads properly
    prompt_manager = PromptManager()
    prompt = prompt_manager.get_prompt("planning", "default_planning")
    assert prompt.version_info.subsystem == "planning"
    assert "project_summary" in prompt.user_prompt_template


def test_planning_translator(mock_planning_output):
    context = PlanningContext(project_name="TestProj")
    telemetry = PlanningTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=10.0,
        cache_hit=True,
        fallback_used=False,
        validation_passed=True,
    )

    session = PlanningTranslator.to_planning_session(
        context, mock_planning_output, telemetry
    )

    assert isinstance(session, PlanningSession)
    assert session.status == "SUCCESS"
    assert session.telemetry == telemetry

    # Assert main CandidateStrategy
    assert len(session.candidates) == 2
    main_cand = session.candidates[0]
    assert main_cand.strategy_name == "LLMPipeline"
    assert main_cand.confidence.confidence_level == "HIGH"
    assert main_cand.confidence.explanation == "Highly recommended for this layout"

    # Assert alternative CandidateStrategy
    alt_cand = session.candidates[1]
    assert alt_cand.strategy_name == "AlternativePipe"
    assert alt_cand.confidence.confidence_level == "MEDIUM"

    # Assert hypotheses mapping
    assert len(session.hypotheses) == 2
    assert session.hypotheses[0].target_component == "LLMPipeline"
    assert (
        "Alternative candidate strategy: AlternativePipe"
        in session.hypotheses[1].description
    )


def test_llm_planning_algorithm_success(mock_planning_output):
    MockProvider.mock_structured_responses[LLMPlanningOutput] = mock_planning_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = LLMPlanningAlgorithm(intelligence_service=service)

    context = PlanningContext(project_name="LLMProj")
    session = algo.plan(context)

    assert isinstance(session, PlanningSession)
    assert session.status == "SUCCESS"
    assert session.selected_execution_strategy.strategy_name == "LLMPipeline"
    assert session.selected_execution_strategy.topological_steps == [
        "impute",
        "scale",
        "train",
    ]
    assert session.telemetry.provider == "mock"
    assert session.telemetry.validation_passed is True
    assert session.telemetry.fallback_used is False


def test_llm_planning_cache_behavior(mock_planning_output, temp_cache_dir):
    MockProvider.mock_structured_responses[LLMPlanningOutput] = mock_planning_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    cache = LLMCache(cache_dir=temp_cache_dir)
    service = IntelligenceService(default_config=config, cache=cache)
    algo = LLMPlanningAlgorithm(intelligence_service=service)

    context = PlanningContext(project_name="LLMProj")

    # First call: Cache miss
    session1 = algo.plan(context)
    assert session1.telemetry.cache_hit is False

    # Second call: Cache hit
    session2 = algo.plan(context)
    assert session2.telemetry.cache_hit is True
    assert (
        session2.selected_execution_strategy.strategy_name
        == session1.selected_execution_strategy.strategy_name
    )


def test_hybrid_planning_algorithm_success(mock_planning_output):
    MockProvider.mock_structured_responses[LLMPlanningOutput] = mock_planning_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = HybridPlanningAlgorithm(intelligence_service=service)

    context = PlanningContext(project_name="HybridProj")
    session = algo.plan(context)

    # Valid output should result in returning the LLM session details
    assert session.selected_execution_strategy.strategy_name == "LLMPipeline"
    assert session.telemetry.validation_passed is True
    assert session.telemetry.fallback_used is False


def test_hybrid_planning_algorithm_validation_failure_fallback(mock_planning_output):
    # Setup output that violates pipeline order (train before scale/impute)
    invalid_output = LLMPlanningOutput(
        strategy_name="LLMPipeline",
        strategy_description="Invalid pipeline",
        topological_steps=["train", "scale", "impute"],  # illegal order
        parameters={"imputer": "median", "scaler": "minmax"},
        confidence=0.9,
        reasoning="Failed order",
        alternative_candidates=[],
        constraints=[],
    )
    MockProvider.mock_structured_responses[LLMPlanningOutput] = invalid_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = HybridPlanningAlgorithm(intelligence_service=service)

    context = PlanningContext(project_name="HybridProj")
    session = algo.plan(context)

    # Validation fails, so we expect fallback to the rule-based strategy
    assert session.selected_execution_strategy.strategy_name == "RuleBasedPipeline"
    assert session.telemetry.validation_passed is False
    assert session.telemetry.fallback_used is True


def test_hybrid_planning_algorithm_provider_exception_fallback():
    # Cause execute to raise an exception by not registering structured response
    # which will cause the basic structured mock generator fallback to instantiate default object.
    # To raise a hard error, let's inject a mock service that raises Exception.
    mock_service = MagicMock(spec=IntelligenceService)
    mock_service.execute_subsystem.side_effect = RuntimeError("LLM Service Unavailable")

    algo = HybridPlanningAlgorithm(intelligence_service=mock_service)
    context = PlanningContext(project_name="HybridProj")

    session = algo.plan(context)

    # Should fall back to RuleBasedPlanningAlgorithm without throwing
    assert session.selected_execution_strategy.strategy_name == "RuleBasedPipeline"
    assert session.telemetry.validation_passed is False
    assert session.telemetry.fallback_used is True


def test_knowledge_derived_constraints_override():
    # Output is minmax scaler
    mock_output = LLMPlanningOutput(
        strategy_name="LLMPipeline",
        strategy_description="Standard",
        topological_steps=["impute", "scale", "train"],
        parameters={"imputer": "mean", "scaler": "minmax"},
        confidence=0.9,
        reasoning="Okay",
        alternative_candidates=[],
        constraints=[],
    )
    MockProvider.mock_structured_responses[LLMPlanningOutput] = mock_output

    config = ProviderConfig(provider="mock", model="mock-gpt")
    service = IntelligenceService(default_config=config)
    algo = HybridPlanningAlgorithm(intelligence_service=service)

    # Let's create a knowledge summary rule that forbids minmax scaler
    # default allowed scalers: "standard,minmax,robust,maxabs"
    # Override allowed_scalers to only allow standard
    rule = ActiveRuleSummary(
        subsystem="planning",
        component="validation_constraints",
        parameters={"allowed_scalers": "standard"},
    )
    context = PlanningContext(
        project_name="HybridProj",
        knowledge_summary=KnowledgeSummary(rules=(rule,)),
    )

    session = algo.plan(context)

    # Since minmax is now forbidden, hybrid validator should fail, triggering fallback
    assert session.selected_execution_strategy.strategy_name == "RuleBasedPipeline"
    assert session.telemetry.validation_passed is False
    assert session.telemetry.fallback_used is True


def test_config_loading_defaults():
    cfg = get_planner_config()
    # If no active project root/config on disk, returns {}
    assert isinstance(cfg, dict)


def test_backward_compatibility():
    # Ensure that empty telemetry field is backward compatible and defaults to None
    session = PlanningSession(
        context=PlanningContext(project_name="CompatProj"),
        status="SUCCESS",
    )
    assert session.telemetry is None


from unittest.mock import patch
import argparse
from pathlib import Path
from mlos.cli.commands.plan import PlanCommand
from mlos.engine.engine import MLOSEngine
from mlos.planning.algorithms.rule_based_algorithm import RuleBasedPlanningAlgorithm


@patch("mlos.cli.commands.plan.find_project_root")
@patch("mlos.cli.commands.plan.reconstruct_project_memory")
@patch("mlos.cli.commands.plan.update_project_config_from_memory")
def test_cli_plan_command_modes(mock_update, mock_reconstruct, mock_find_root):
    mock_find_root.return_value = Path("/dummy")
    from mlos.domain.models.project_memory import ProjectMemory

    memory = ProjectMemory(project_name="CliProj", project_goal="CliGoal")
    mock_reconstruct.return_value = memory

    engine = MLOSEngine()
    # Mock planning engine's plan call to return a valid session
    mock_session = MagicMock(spec=PlanningSession)
    mock_session.hypotheses = []
    mock_session.candidates = []
    mock_session.selected_execution_strategy = None
    mock_session.telemetry = PlanningTelemetry(
        provider="mock",
        model="mock-gpt",
        latency_ms=1.2,
        cache_hit=False,
        fallback_used=False,
        validation_passed=True,
    )
    engine.plan = MagicMock(return_value=mock_session)

    cmd = PlanCommand()

    # Test --rule
    args = argparse.Namespace(rule=True, llm=False, hybrid=False)
    exit_code = cmd.handle(args, engine)
    assert exit_code == 0
    assert isinstance(
        engine.planning_engine.planning_algorithm, RuleBasedPlanningAlgorithm
    )

    # Test --llm
    args = argparse.Namespace(rule=False, llm=True, hybrid=False)
    exit_code = cmd.handle(args, engine)
    assert exit_code == 0
    assert isinstance(engine.planning_engine.planning_algorithm, LLMPlanningAlgorithm)

    # Test --hybrid
    args = argparse.Namespace(rule=False, llm=False, hybrid=True)
    exit_code = cmd.handle(args, engine)
    assert exit_code == 0
    assert isinstance(
        engine.planning_engine.planning_algorithm, HybridPlanningAlgorithm
    )
