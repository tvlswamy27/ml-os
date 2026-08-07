"""
Unit and Integration Tests for ML-OS v2.3 Meta-Reasoning & Cognitive Orchestrator.

Author: Antigravity
License: MIT
"""

import uuid
from datetime import datetime

import pytest

from mlos.domain.enums.execution_lifecycle import ExecutionLifecycle
from mlos.domain.enums.subsystem_name import SubsystemName
from mlos.domain.models.meta_reasoning import (
    ExecutionConstraints,
    ExecutionPlan,
    ExecutionSchedule,
    HistoricalEvidence,
    MetaContext,
    MetaReasoningState,
    PolicyVersion,
    ProviderCapability,
    ResourceAllocation,
    ScheduleDependency,
    ScheduleNode,
)
from mlos.domain.models.project_memory import ProjectMemory
from mlos.engine.engine import MLOSEngine
from mlos.meta_reasoning.communication.execution_event_bus import ExecutionEventBus
from mlos.meta_reasoning.dispatchers.execution_dispatcher import ExecutionDispatcher
from mlos.meta_reasoning.meta_planner import MetaPlanner, RuleBasedMetaAlgorithm
from mlos.meta_reasoning.optimization.optimization_strategy import (
    WeightedScoreOptimization,
)
from mlos.meta_reasoning.routing.provider_selection_strategy import (
    HybridProviderSelector,
)
from mlos.meta_reasoning.scheduling.execution_scheduler import ExecutionScheduler
from mlos.meta_reasoning.simulation.execution_simulator import ExecutionSimulator
from mlos.meta_reasoning.validation.dry_run_verifier import DryRunVerifier
from mlos.meta_reasoning.validation.execution_plan_validator import (
    ExecutionPlanValidator,
    PlanValidationError,
)


@pytest.fixture
def mock_context() -> MetaContext:
    from mlos.domain.models.knowledge_summary import KnowledgeSummary

    return MetaContext(
        project_name="TestProject",
        project_goal="TestGoal",
        dataset_summary=None,
        feature_session=None,
        knowledge_summary=KnowledgeSummary(),
        provider_registry=(
            ProviderCapability(
                "openai",
                "gpt-4o",
                True,
                True,
                True,
                True,
                128000,
                0.4,
                0.005,
                0.015,
                False,
            ),
            ProviderCapability(
                "local",
                "llama-3-8b",
                True,
                False,
                False,
                False,
                8000,
                0.2,
                0.0,
                0.0,
                True,
            ),
        ),
        user_constraints=ResourceAllocation(
            token_budget=50000,
            cost_budget_usd=0.5,
            cpu_cores_limit=1.0,
            memory_limit_mb=512,
        ),
        feedback_evidence=HistoricalEvidence(),
        observed_at=datetime.utcnow(),
    )


def test_domain_model_creation():
    constraints = ExecutionConstraints(
        max_cost=1.0,
        max_tokens=10000,
        max_latency=5000.0,
        max_cpu=2.0,
        max_memory=1024.0,
        minimum_quality=0.7,
        maximum_retry_depth=3,
        must_use_local_models=False,
        allow_network_calls=True,
        allow_parallel_execution=False,
    )
    assert constraints.max_cost == 1.0
    assert not constraints.must_use_local_models


def test_provider_selection(mock_context):
    selector = HybridProviderSelector()
    pc = selector.select_provider(SubsystemName.PLANNING, mock_context)
    assert pc is not None
    assert pc.provider_name in ("openai", "local")


def test_optimization_and_planner(mock_context):
    selector = HybridProviderSelector()
    optimizer = WeightedScoreOptimization(selector)
    algo = RuleBasedMetaAlgorithm(optimizer)
    planner = MetaPlanner(algo)

    session = planner.plan(mock_context)
    assert session.execution_lifecycle == ExecutionLifecycle.PLANNED
    assert session.reasoning_state.execution_plan is not None
    assert session.reasoning_state.execution_plan.checksum != ""


def test_validator(mock_context):
    selector = HybridProviderSelector()
    optimizer = WeightedScoreOptimization(selector)
    algo = RuleBasedMetaAlgorithm(optimizer)
    plan = algo.generate_plan(mock_context, MetaReasoningState())

    validator = ExecutionPlanValidator()
    constraints = ExecutionConstraints(
        max_cost=10.0,
        max_tokens=1000000,
        max_latency=100000.0,
        max_cpu=8.0,
        max_memory=16384.0,
        minimum_quality=0.0,
        maximum_retry_depth=3,
        must_use_local_models=False,
        allow_network_calls=True,
        allow_parallel_execution=True,
    )
    # Should validate successfully
    validator.validate(plan, constraints)


def test_unreachable_node_validator_error():
    pv = PolicyVersion(
        uuid.uuid4(), 1, None, "test", datetime.utcnow(), None, datetime.utcnow()
    )
    nodes = (
        ScheduleNode("node_planning", SubsystemName.PLANNING, "ALWAYS", False),
        ScheduleNode("node_decision", SubsystemName.DECISION, "ALWAYS", False),
    )
    # DAG has 2 nodes but a dependency references a node not in list
    dependencies = (ScheduleDependency("node_planning", "node_invalid", "SEQUENTIAL"),)
    schedule = ExecutionSchedule(nodes, dependencies, 1)
    plan = ExecutionPlan(
        policy_version=pv,
        subsystem_policies={},
        execution_schedule=schedule,
        optimization_result={},
        planner_name="test",
        planner_version="1.0",
        generated_at=datetime.utcnow(),
        checksum="123",
    )

    validator = ExecutionPlanValidator()
    constraints = ExecutionConstraints(
        max_cost=1.0,
        max_tokens=1000,
        max_latency=100.0,
        max_cpu=1.0,
        max_memory=100.0,
        minimum_quality=0.0,
        maximum_retry_depth=1,
        must_use_local_models=False,
        allow_network_calls=True,
        allow_parallel_execution=False,
    )
    with pytest.raises(PlanValidationError):
        validator.validate(plan, constraints)


def test_cycle_detection_validator_error():
    pv = PolicyVersion(
        uuid.uuid4(), 1, None, "test", datetime.utcnow(), None, datetime.utcnow()
    )
    nodes = (
        ScheduleNode("node_planning", SubsystemName.PLANNING, "ALWAYS", False),
        ScheduleNode("node_decision", SubsystemName.DECISION, "ALWAYS", False),
    )
    # A cycle: planning -> decision -> planning
    dependencies = (
        ScheduleDependency("node_planning", "node_decision", "SEQUENTIAL"),
        ScheduleDependency("node_decision", "node_planning", "SEQUENTIAL"),
    )
    schedule = ExecutionSchedule(nodes, dependencies, 1)
    plan = ExecutionPlan(
        policy_version=pv,
        subsystem_policies={},
        execution_schedule=schedule,
        optimization_result={},
        planner_name="test",
        planner_version="1.0",
        generated_at=datetime.utcnow(),
        checksum="123",
    )

    validator = ExecutionPlanValidator()
    constraints = ExecutionConstraints(
        max_cost=1.0,
        max_tokens=1000,
        max_latency=100.0,
        max_cpu=1.0,
        max_memory=100.0,
        minimum_quality=0.0,
        maximum_retry_depth=1,
        must_use_local_models=False,
        allow_network_calls=True,
        allow_parallel_execution=False,
    )
    with pytest.raises(PlanValidationError):
        validator.validate(plan, constraints)


def test_simulation_and_dry_run(mock_context):
    selector = HybridProviderSelector()
    optimizer = WeightedScoreOptimization(selector)
    algo = RuleBasedMetaAlgorithm(optimizer)
    plan = algo.generate_plan(mock_context, MetaReasoningState())

    simulator = ExecutionSimulator()
    report = simulator.simulate(plan, mock_context)
    assert report.estimated_runtime_ms > 0.0
    assert report.success_probability == 0.95

    verifier = DryRunVerifier()
    verifier.verify_environment(plan, mock_context)


def test_event_bus_and_scheduler(mock_context):
    event_bus = ExecutionEventBus()
    events_triggered = []

    def observer(event):
        events_triggered.append(event.event_type)

    event_bus.subscribe("PlanGenerated", observer)
    event_bus.subscribe("PlanCompleted", observer)

    engine = MLOSEngine()
    memory = ProjectMemory(project_name="Test", project_goal="Goal")
    engine.project_memory = memory

    dispatcher = ExecutionDispatcher(engine, event_bus)
    # Mock dispatch_subsystem to isolate scheduler testing
    dispatcher.dispatch_subsystem = (
        lambda subsystem_name, strategy: ExecutionLifecycle.COMPLETED
    )
    scheduler = ExecutionScheduler(dispatcher, event_bus)

    selector = HybridProviderSelector()
    optimizer = WeightedScoreOptimization(selector)
    algo = RuleBasedMetaAlgorithm(optimizer)
    plan = algo.generate_plan(mock_context, MetaReasoningState())

    snapshot = scheduler.execute_schedule(plan, mock_context)
    assert snapshot.run_id is not None
    assert "PlanGenerated" in events_triggered
    assert "PlanCompleted" in events_triggered
