from datetime import datetime

from mlos.decision.decision_engine import DecisionEngine
from mlos.domain.models.knowledge.knowledge_confidence import KnowledgeConfidence
from mlos.domain.models.knowledge.knowledge_entry import KnowledgeEntry
from mlos.domain.models.knowledge.knowledge_entry_type import KnowledgeEntryType
from mlos.domain.models.knowledge.knowledge_status import KnowledgeStatus
from mlos.domain.models.knowledge.knowledge_version import KnowledgeVersion
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.services.decision_service import DecisionService
from mlos.domain.services.planning_service import PlanningService
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.planning.algorithms.rule_based_algorithm import RuleBasedPlanningAlgorithm
from mlos.planning.planning_engine import PlanningEngine


def test_empty_knowledge_repository_preserves_behavior():
    """Verify that projects without any active knowledge execute with existing defaults."""
    pm_service = ProjectMemoryService()
    planning_service = PlanningService(
        PlanningEngine(RuleBasedPlanningAlgorithm()), pm_service
    )
    decision_service = DecisionService(DecisionEngine(), pm_service)

    memory = ProjectMemory(
        project_name="No-Knowledge-Proj", project_goal="Supervised regression goal"
    )

    # Execute default planning
    p_session = planning_service.plan(memory)
    assert p_session.selected_execution_strategy is not None
    # Default parameters should match existing defaults
    assert p_session.selected_execution_strategy.parameters == {
        "imputer": "mean",
        "scaler": "standard",
    }
    assert p_session.selected_execution_strategy.topological_steps == [
        "impute",
        "scale",
        "train",
    ]

    # Setup dummy dataset for decision
    from mlos.domain.models.dataset import Dataset

    memory.dataset = Dataset(
        path="test.csv",
        rows=100,
        columns=["age", "salary"],
        missing_values={"age": 5, "salary": 0},
        missing_percentages={"age": 0.05, "salary": 0.0},
        column_types={"age": "numerical", "salary": "numerical"},
        categorical_columns=[],
        numerical_columns=["age", "salary"],
        duplicate_rows=0,
    )

    # Execute default decision making
    decisions = decision_service.decide(memory)
    # Default imputer should be MEDIAN_IMPUTATION (due to numerical)
    age_dec = [d for d in decisions if "age" in d.title][0]
    assert age_dec.strategy == "Median Imputation"


def test_active_rules_override_defaults_deprecated_rules_ignored():
    """Verify ACTIVE rules override default parameters while DEPRECATED/EXPERIMENTAL rules are ignored."""
    pm_service = ProjectMemoryService()
    planning_service = PlanningService(
        PlanningEngine(RuleBasedPlanningAlgorithm()), pm_service
    )
    decision_service = DecisionService(DecisionEngine(), pm_service)

    memory = ProjectMemory(project_name="Override-Proj", project_goal="Supervised goal")

    # 1. Add an ACTIVE planning rule (override scaler to minmax)
    active_plan_rule = KnowledgeEntry(
        knowledge_id="active-rule-id-1",
        knowledge_type=KnowledgeEntryType.PARAMETER_PRIOR,
        target_subsystem="planning",
        target_component="rule_based_planner",
        parameters={"scaler": "minmax"},
        source_learning_sessions=(),
        evidence_summary="",
        version=KnowledgeVersion(1, None, datetime.now(), "", ""),
        created_at=datetime.now(),
        last_used=None,
        usage_count=0,
        confidence=KnowledgeConfidence(1.0, 0.0, 1, 0, ""),
        status=KnowledgeStatus.ACTIVE,
    )
    memory.knowledge_entries.append(active_plan_rule)

    # 2. Add a DEPRECATED planning rule (would override imputer to constant, but should be ignored)
    deprecated_plan_rule = KnowledgeEntry(
        knowledge_id="dep-rule-id",
        knowledge_type=KnowledgeEntryType.PARAMETER_PRIOR,
        target_subsystem="planning",
        target_component="rule_based_planner",
        parameters={"imputer": "constant"},
        source_learning_sessions=(),
        evidence_summary="",
        version=KnowledgeVersion(1, None, datetime.now(), "", ""),
        created_at=datetime.now(),
        last_used=None,
        usage_count=0,
        confidence=KnowledgeConfidence(1.0, 0.0, 1, 0, ""),
        status=KnowledgeStatus.DEPRECATED,
    )
    memory.knowledge_entries.append(deprecated_plan_rule)

    # 3. Add an ACTIVE decision rule (override imputer strategy to most_frequent for 'age')
    active_dec_rule = KnowledgeEntry(
        knowledge_id="active-rule-id-2",
        knowledge_type=KnowledgeEntryType.PARAMETER_PRIOR,
        target_subsystem="decision",
        target_component="missing_value",
        parameters={"age": "Most Frequent Imputation"},
        source_learning_sessions=(),
        evidence_summary="",
        version=KnowledgeVersion(1, None, datetime.now(), "", ""),
        created_at=datetime.now(),
        last_used=None,
        usage_count=0,
        confidence=KnowledgeConfidence(1.0, 0.0, 1, 0, ""),
        status=KnowledgeStatus.ACTIVE,
    )
    memory.knowledge_entries.append(active_dec_rule)

    # Run Planning
    p_session = planning_service.plan(memory)
    # The active scaler parameter should be overridden to 'minmax'
    # The deprecated imputer parameter 'constant' should be IGNORED (retaining default 'mean')
    assert p_session.selected_execution_strategy.parameters["scaler"] == "minmax"
    assert p_session.selected_execution_strategy.parameters["imputer"] == "mean"

    # Setup dummy dataset for decision
    from mlos.domain.models.dataset import Dataset

    memory.dataset = Dataset(
        path="test.csv",
        rows=100,
        columns=["age", "salary"],
        missing_values={"age": 5, "salary": 0},
        missing_percentages={"age": 0.05, "salary": 0.0},
        column_types={"age": "numerical", "salary": "numerical"},
        categorical_columns=[],
        numerical_columns=["age", "salary"],
        duplicate_rows=0,
    )

    # Run Decision
    decisions = decision_service.decide(memory)
    age_dec = [d for d in decisions if "age" in d.title][0]
    # Imputer should be overridden to "Most Frequent Imputation" instead of default "Median Imputation"
    assert age_dec.strategy == "Most Frequent Imputation"
    assert "active knowledge rule" in age_dec.reason.lower()


def test_knowledge_repository_read_only_downstream():
    """Verify that Planning and Decision do not mutate the ProjectMemory knowledge lists."""
    pm_service = ProjectMemoryService()
    planning_service = PlanningService(
        PlanningEngine(RuleBasedPlanningAlgorithm()), pm_service
    )
    decision_service = DecisionService(DecisionEngine(), pm_service)

    memory = ProjectMemory(
        project_name="Read-Only-Proj", project_goal="Ensure no mutations"
    )

    # Ensure empty entries
    assert len(memory.knowledge_entries) == 0

    planning_service.plan(memory)
    # Planning must not insert anything
    assert len(memory.knowledge_entries) == 0

    decision_service.decide(memory)
    # Decision must not insert anything
    assert len(memory.knowledge_entries) == 0
