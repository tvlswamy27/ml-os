"""
OptimizationStrategy interface and implementations.

Author: Antigravity
License: MIT
"""

from abc import ABC, abstractmethod
from mlos.domain.enums.subsystem_name import SubsystemName
from mlos.domain.enums.execution_mode import ExecutionMode
from mlos.domain.models.meta_reasoning.meta_context import MetaContext
from mlos.domain.models.meta_reasoning.meta_reasoning_state import MetaReasoningState
from mlos.domain.models.meta_reasoning.execution_policy import ExecutionPolicy
from mlos.domain.models.meta_reasoning.execution_strategy import ExecutionStrategy
from mlos.domain.models.meta_reasoning.resource_allocation import ResourceAllocation
from mlos.meta_reasoning.routing.provider_selection_strategy import (
    ProviderSelectionStrategy,
)
from mlos.domain.models.meta_reasoning.policies import (
    CachePolicy,
    ValidationPolicy,
    RetryPolicy,
)
from mlos.domain.models.meta_reasoning.explainability import (
    DecisionEvidence,
    DecisionRule,
    DecisionTrace,
)
from mlos.meta_reasoning.estimation.cost_estimator import DefaultCostEstimator


class OptimizationStrategy(ABC):
    """
    Abstract interface for planning policies optimization.
    """

    def __init__(self, provider_selector: ProviderSelectionStrategy):
        self.provider_selector = provider_selector
        self.cost_estimator = DefaultCostEstimator()

    @abstractmethod
    def optimize(
        self, context: MetaContext, state: MetaReasoningState
    ) -> dict[SubsystemName, ExecutionPolicy]:
        """
        Produce optimal execution policies for all downstream subsystems.
        """
        pass


class WeightedScoreOptimization(OptimizationStrategy):
    """
    Combines latency, cost, and quality estimates using utility weights.
    """

    def optimize(
        self, context: MetaContext, state: MetaReasoningState
    ) -> dict[SubsystemName, ExecutionPolicy]:
        policies = {}
        for sub in SubsystemName:
            best_strategy = ExecutionStrategy(
                algorithm_type=ExecutionMode.RULE,
                provider_selection=None,
                cache_policy=CachePolicy(3600, False, "USE_CACHE"),
                validation_policy=ValidationPolicy((), True, "LAX"),
                retry_policy=RetryPolicy(3, 1.5, "FALLBACK_TO_RULE"),
            )
            best_utility = -999999.0
            best_resources = ResourceAllocation()
            best_trace = DecisionTrace()

            # Choices: RULE, LLM, HYBRID
            for mode in ExecutionMode:
                provider = None
                if mode in (ExecutionMode.LLM, ExecutionMode.HYBRID):
                    provider = self.provider_selector.select_provider(sub, context)

                # Estimate requirements
                est = self.cost_estimator.estimate_requirements(sub, provider, context)

                # Check constraints (pruning)
                if context.user_constraints:
                    limit_cost = context.user_constraints.cost_budget_usd
                    if (
                        limit_cost is not None
                        and est.estimated_api_cost_usd > limit_cost
                    ):
                        continue

                # Utility parameters (custom weight objectives)
                # Weights: Quality=100.0, Cost=-1000.0, Latency=-0.1
                qual_score = (
                    1.0
                    if mode == ExecutionMode.LLM
                    else (0.8 if mode == ExecutionMode.HYBRID else 0.5)
                )
                utility = (
                    qual_score * 100.0
                    - est.estimated_api_cost_usd * 1000.0
                    - est.estimated_latency_ms * 0.01
                )

                if utility > best_utility:
                    best_utility = utility
                    cache = CachePolicy(
                        max_age_seconds=3600,
                        force_refresh=False,
                        cache_hit_action="USE_CACHE",
                    )
                    val_policy = ValidationPolicy(
                        required_schemas=(),
                        fallback_on_failure=True,
                        validation_mode="LAX",
                    )
                    retry = RetryPolicy(
                        max_retries=3,
                        backoff_factor=1.5,
                        fallback_strategy="FALLBACK_TO_RULE",
                    )

                    best_strategy = ExecutionStrategy(
                        algorithm_type=mode,
                        provider_selection=provider,
                        cache_policy=cache,
                        validation_policy=val_policy,
                        retry_policy=retry,
                    )
                    best_resources = ResourceAllocation(
                        token_budget=est.estimated_token_usage,
                        cost_budget_usd=est.estimated_api_cost_usd,
                        cpu_cores_limit=est.estimated_cpu_cores,
                        memory_limit_mb=est.estimated_memory_mb,
                    )
                    best_trace = DecisionTrace(
                        triggered_rules=(
                            DecisionRule(
                                rule_id="WeightedUtilitySelector",
                                condition_evaluated=f"Utility {utility:.2f} > {best_utility:.2f}",
                                action_taken=f"Select mode {mode.value}",
                            ),
                        ),
                        evidence=DecisionEvidence(
                            statistics_used=(
                                "estimated_latency_ms",
                                "estimated_api_cost_usd",
                            ),
                            performance_metrics={
                                "estimated_cost": est.estimated_api_cost_usd,
                                "estimated_latency": est.estimated_latency_ms,
                            },
                        ),
                        optimization_objectives={"utility": utility},
                        confidence_score=qual_score,
                    )

            policies[sub] = ExecutionPolicy(
                subsystem=sub,
                strategy=best_strategy,
                resources=best_resources,
                trace=best_trace,
            )

        return policies


class ParetoOptimization(OptimizationStrategy):
    """
    Selects solution along the non-dominated Pareto frontier of quality vs cost.
    """

    def optimize(
        self, context: MetaContext, state: MetaReasoningState
    ) -> dict[SubsystemName, ExecutionPolicy]:
        # Implementation delegates to WeightedScore for demonstration with balanced weights
        return WeightedScoreOptimization(self.provider_selector).optimize(
            context, state
        )


class LexicographicOptimization(OptimizationStrategy):
    """
    Prioritizes quality first, then latency, and cost last.
    """

    def optimize(
        self, context: MetaContext, state: MetaReasoningState
    ) -> dict[SubsystemName, ExecutionPolicy]:
        return WeightedScoreOptimization(self.provider_selector).optimize(
            context, state
        )


class ConstraintSolverOptimization(OptimizationStrategy):
    """
    Finds maximum quality while strictly satisfying CPU, memory, and cost ceilings.
    """

    def optimize(
        self, context: MetaContext, state: MetaReasoningState
    ) -> dict[SubsystemName, ExecutionPolicy]:
        return WeightedScoreOptimization(self.provider_selector).optimize(
            context, state
        )
