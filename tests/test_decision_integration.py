"""
Unit and integration tests for Planning and Decision integration.
"""

from unittest.mock import MagicMock

from mlos.decision.decision_engine import DecisionEngine
from mlos.decision.strategies.missing_value_decision import MissingValueDecision
from mlos.domain.models.dataset import Dataset
from mlos.domain.models.decision import Decision
from mlos.domain.models.decision_context import DecisionContext
from mlos.domain.models.planning.execution_strategy import ExecutionStrategy
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.services.decision_service import DecisionService
from mlos.domain.services.project_memory_service import ProjectMemoryService


def test_decision_context_resolution():
    """
    Verify DecisionContext resolves the latest ExecutionStrategy from planning_sessions.
    """
    memory = ProjectMemory(project_name="TestProj", project_goal="TestGoal")

    # 1. Without planning sessions
    service = DecisionService(MagicMock(spec=DecisionEngine), ProjectMemoryService())
    ctx = service.build_context(memory)
    assert ctx.project_memory == memory
    assert ctx.execution_strategy is None

    # 2. With planning sessions
    from mlos.domain.models.planning.planning_context import PlanningContext

    strategy = ExecutionStrategy(
        strategy_name="RuleBasedPipeline",
        topological_steps=["impute", "encode"],
        parameters={"scaler": "minmax"},
    )
    session = PlanningSession(
        context=PlanningContext(project_name="TestProj"),
        status="SUCCESS",
        observations=(),
        hypotheses=(),
        candidates=(),
        selected_execution_strategy=strategy,
    )
    memory.planning_sessions.append(session)

    ctx2 = service.build_context(memory)
    assert ctx2.execution_strategy == strategy


def test_decision_service_decide_orchestration():
    """
    Verify that DecisionService.decide() calls build_context, run_decisions,
    persists decisions, and returns them.
    """
    memory = ProjectMemory(project_name="TestProj", project_goal="TestGoal")

    mock_engine = MagicMock(spec=DecisionEngine)
    decisions = [
        Decision(title="Dec1", strategy="Impute", confidence="High", reason="Test")
    ]
    mock_engine.decide.return_value = decisions

    mem_service = ProjectMemoryService()
    service = DecisionService(mock_engine, mem_service)

    res = service.decide(memory)

    assert res == decisions
    assert len(memory.decisions) == 1
    assert memory.decisions[0] == decisions[0]


def test_decision_engine_skipping_logic():
    """
    Verify that decision strategies are skipped if their mapped step name is omitted
    from ExecutionStrategy.topological_steps.
    """
    dataset = Dataset(
        path="dummy.csv",
        rows=100,
        columns=5,
        target="target",
        missing_values={"col1": 10},
        missing_percentages={"col1": 10.0},
        column_types={"col1": "numerical"},
    )
    memory = ProjectMemory(
        project_name="SkipProj",
        project_goal="Test",
        dataset=dataset,
    )

    # Strategy with impute only (scale and encode are omitted)
    strategy = ExecutionStrategy(
        strategy_name="RuleBasedPipeline",
        topological_steps=["impute"],  # Omit "scale", "encode", etc.
        parameters={},
    )

    engine = DecisionEngine()

    # 1. Run with planning (scale/encode skipped, impute runs)
    ctx = DecisionContext(project_memory=memory, execution_strategy=strategy)
    decisions = engine.decide(ctx)

    # MissingValueDecision is mapped to "impute", should produce decisions
    impute_decisions = [d for d in decisions if "Missing Value" in d.title]
    assert len(impute_decisions) > 0

    # ScalingDecision is mapped to "scale" (omitted from topological_steps), should not run
    scale_decisions = [d for d in decisions if "Scaling" in d.title]
    assert len(scale_decisions) == 0

    # 2. Run without planning (all registered strategies run, backwards-compatible)
    ctx_none = DecisionContext(project_memory=memory, execution_strategy=None)
    decisions_none = engine.decide(ctx_none)

    assert len(decisions_none) > 0


def test_decision_strategy_backward_compatibility():
    """
    Verify concrete strategies run successfully when direct ProjectMemory is passed
    instead of DecisionContext.
    """
    dataset = Dataset(
        path="dummy.csv",
        rows=100,
        columns=5,
        target="target",
        missing_values={"col1": 10},
        missing_percentages={"col1": 10.0},
        column_types={"col1": "numerical"},
    )
    memory = ProjectMemory(
        project_name="LegacyProj",
        project_goal="Test",
        dataset=dataset,
    )

    strat = MissingValueDecision()
    decisions = strat.decide(memory)  # direct call with memory
    assert len(decisions) > 0
