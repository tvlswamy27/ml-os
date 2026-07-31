"""
HybridPlanningAlgorithm implementation.

Author: Vikram Tanakala
License: MIT
"""

from typing import Any
from mlos.planning.algorithms.planning_algorithm import PlanningAlgorithm
from mlos.planning.algorithms.rule_based_algorithm import RuleBasedPlanningAlgorithm
from mlos.planning.algorithms.llm_planning_algorithm import LLMPlanningAlgorithm
from mlos.domain.models.planning.planning_context import PlanningContext
from mlos.domain.models.planning.planning_session import PlanningSession
from mlos.domain.models.planning.hypothesis import Hypothesis
from mlos.domain.models.planning.candidate_strategy import CandidateStrategy
from mlos.domain.models.planning.execution_strategy import ExecutionStrategy
from mlos.domain.models.planning.reasoning_state import ReasoningState
from mlos.domain.models.planning.constraint import Constraint
from mlos.domain.models.planning.planning_telemetry import PlanningTelemetry
from mlos.intelligence.validation.hybrid_validator import HybridValidator
from mlos.intelligence.intelligence_service import IntelligenceService

DEFAULT_VALIDATION_CONSTRAINTS = {
    "allowed_steps": "impute,scale,encode,split,train",
    "allowed_scalers": "standard,minmax,robust,maxabs",
    "allowed_imputers": "mean,median,most_frequent,constant",
    "allowed_duplicate_handling": "drop,keep,ignore",
    "test_size_min": "0.05",
    "test_size_max": "0.5",
    "train_size_min": "0.5",
    "train_size_max": "0.95",
}


class HybridPlanningAlgorithm(PlanningAlgorithm):
    """
    Hybrid planning algorithm combining rule-based baselines with LLM planners,
    performing validation checking and automated fallback.
    """

    def __init__(self, intelligence_service: IntelligenceService | None = None):
        """
        Initialize the hybrid algorithm with rule-based and LLM sub-planners.
        """
        self.rule_based_planner = RuleBasedPlanningAlgorithm()
        self.llm_planner = LLMPlanningAlgorithm(
            intelligence_service=intelligence_service
        )

    def can_plan(self, context: PlanningContext) -> bool:
        """
        Hybrid planner can plan for any context.
        """
        return True

    def plan(self, context: PlanningContext) -> PlanningSession:
        """
        Runs rule-based baseline, passes it as context constraint, calls LLM,
        validates output, and falls back to baseline if validations fail or LLM throws.
        """
        # 1. Run baseline rule-based planner
        try:
            baseline_session = self.rule_based_planner.plan(context)
        except Exception:
            baseline_session = None

        # 2. Formulate baseline constraint details
        baseline_constraints = []
        if baseline_session and baseline_session.selected_execution_strategy:
            strategy = baseline_session.selected_execution_strategy
            baseline_info = (
                f"Baseline Strategy Name: {strategy.strategy_name}, "
                f"Steps: {', '.join(strategy.topological_steps)}, "
                f"Parameters: {strategy.parameters}"
            )
            baseline_constraints.append(
                Constraint(
                    name="baseline_strategy",
                    limit_type="baseline",
                    limit_value=baseline_info,
                )
            )

        # Inject baseline details as a new constraint in the context
        new_constraints = tuple(list(context.constraints) + baseline_constraints)
        llm_context = PlanningContext(
            project_name=context.project_name,
            goals=context.goals,
            constraints=new_constraints,
            observations=context.observations,
            assumptions=context.assumptions,
            knowledge_summary=context.knowledge_summary,
        )

        llm_session = None
        validation_passed = False

        # 3. Invoke LLM planning algorithm
        try:
            llm_session = self.llm_planner.plan(llm_context)

            # 4. Programmatic Validation
            def constraint_checker(session: PlanningSession) -> bool:
                strategy = session.selected_execution_strategy
                if not strategy:
                    return False
                return self._validate_constraints(strategy, context)

            validated_session, validation_passed = HybridValidator.validate_constraints(
                parsed_output=llm_session,
                constraint_checker=constraint_checker,
                fallback_value=baseline_session,
            )
        except Exception:
            validation_passed = False
            validated_session = baseline_session

        # 5. Build and attach telemetry
        # Extract telemetry details from LLM planner if available
        llm_telemetry = (
            self.llm_planner._last_telemetry
            if hasattr(self.llm_planner, "_last_telemetry")
            else None
        )

        token_usage = {}
        if llm_telemetry and llm_telemetry.token_usage:
            token_usage = dict(llm_telemetry.token_usage)
        else:
            token_usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }

        # Check if fallback was used
        fallback_used = not validation_passed

        hybrid_telemetry = PlanningTelemetry(
            provider=(llm_telemetry.provider if llm_telemetry else "mock"),
            model=(llm_telemetry.model if llm_telemetry else "mock-gpt"),
            latency_ms=(llm_telemetry.latency_ms if llm_telemetry else 0.0),
            cache_hit=(llm_telemetry.cache_hit if llm_telemetry else False),
            fallback_used=fallback_used,
            validation_passed=validation_passed,
            request_id=(llm_telemetry.request_id if llm_telemetry else ""),
            token_usage=token_usage,
            estimated_cost=(llm_telemetry.estimated_cost if llm_telemetry else 0.0),
        )

        # Build final PlanningSession referencing PlanningTelemetry
        target_session = (
            llm_session if (validation_passed and llm_session) else baseline_session
        )

        # Fallback to an empty template session if rule-based also failed to return one
        if not target_session:
            return PlanningSession(
                context=context,
                status="FAILURE",
                telemetry=hybrid_telemetry,
            )

        return PlanningSession(
            context=context,
            status=target_session.status,
            observations=target_session.observations,
            hypotheses=target_session.hypotheses,
            candidates=target_session.candidates,
            selected_execution_strategy=target_session.selected_execution_strategy,
            telemetry=hybrid_telemetry,
        )

    def _get_validation_constraints(self, context: PlanningContext) -> dict[str, str]:
        """
        Merge default constraints with any active knowledge rules.
        """
        constraints = dict(DEFAULT_VALIDATION_CONSTRAINTS)
        for rule in context.knowledge_summary.rules:
            if (
                rule.subsystem == "planning"
                and rule.component == "validation_constraints"
            ):
                for k, v in rule.parameters.items():
                    constraints[k] = v
        return constraints

    def _validate_constraints(
        self, strategy: ExecutionStrategy, context: PlanningContext
    ) -> bool:
        """
        Validate execution strategy parameters and pipeline order against active constraints.
        """
        constraints = self._get_validation_constraints(context)

        # 1. Preprocessing steps check
        allowed_steps = {
            step.strip() for step in constraints["allowed_steps"].split(",")
        }
        steps = strategy.topological_steps
        if not steps:
            return False

        for step in steps:
            if step not in allowed_steps:
                return False

        # Parameters checks
        params = strategy.parameters or {}

        # 2. Scalers check
        allowed_scalers = {s.strip() for s in constraints["allowed_scalers"].split(",")}
        scaler = params.get("scaler")
        if scaler and scaler not in allowed_scalers:
            return False

        # 3. Imputers check
        allowed_imputers = {
            imp.strip() for imp in constraints["allowed_imputers"].split(",")
        }
        imputer = params.get("imputer")
        if imputer and imputer not in allowed_imputers:
            return False

        # 4. Duplicate handling check
        allowed_dup = {
            dup.strip() for dup in constraints["allowed_duplicate_handling"].split(",")
        }
        duplicate_handling = params.get("duplicate_handling")
        if duplicate_handling and duplicate_handling not in allowed_dup:
            return False

        # 5 & 6. Parameter ranges check (test_size and train_size)
        if "test_size" in params:
            try:
                val = float(params["test_size"])
                min_val = float(constraints["test_size_min"])
                max_val = float(constraints["test_size_max"])
                if not (min_val <= val <= max_val):
                    return False
            except ValueError:
                return False

        if "train_size" in params:
            try:
                val = float(params["train_size"])
                min_val = float(constraints["train_size_min"])
                max_val = float(constraints["train_size_max"])
                if not (min_val <= val <= max_val):
                    return False
            except ValueError:
                return False

        # Check other ranges, e.g. random_state
        if "random_state" in params:
            try:
                val = int(params["random_state"])
                if val < 0:
                    return False
            except ValueError:
                return False

        # 7. No illegal pipeline order check
        indices = {step: idx for idx, step in enumerate(steps)}

        if "impute" in indices and "scale" in indices:
            if indices["impute"] > indices["scale"]:
                return False

        if "train" in indices:
            train_idx = indices["train"]
            for step in ["impute", "scale", "encode", "split"]:
                if step in indices and indices[step] > train_idx:
                    return False

        return True

    # Dummy overrides for Template Method abstract compatibility
    def _analyze_observations(self, context: PlanningContext) -> ReasoningState:
        return ReasoningState(facts={})

    def _generate_hypotheses(self, reasoning_state: ReasoningState) -> list[Hypothesis]:
        return []

    def _generate_candidate_strategies(
        self, hypotheses: list[Hypothesis]
    ) -> list[CandidateStrategy]:
        return []

    def _evaluate_candidate_strategies(
        self, candidates: list[CandidateStrategy], hypotheses: list[Hypothesis]
    ) -> dict[str, float]:
        return {}

    def _enrich_candidates(
        self,
        candidates: list[CandidateStrategy],
        reasoning_state: ReasoningState,
        hypotheses: list[Hypothesis],
    ) -> list[CandidateStrategy]:
        return []

    def _select_final_strategy(
        self, candidates: list[CandidateStrategy], scores: dict[str, float]
    ) -> ExecutionStrategy | None:
        return None

    def _construct_session(
        self,
        context: PlanningContext,
        hypotheses: list[Hypothesis],
        candidates: list[CandidateStrategy],
        selected: ExecutionStrategy | None,
    ) -> PlanningSession:
        # Never called because plan() is fully overridden
        return PlanningSession(context=context, status="SUCCESS")
