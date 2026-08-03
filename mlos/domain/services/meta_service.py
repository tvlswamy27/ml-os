"""
Meta-Reasoning Cognitive Service.

Author: Antigravity
License: MIT
"""

from datetime import datetime
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.knowledge_summary import build_knowledge_summary
from mlos.domain.models.meta_reasoning.meta_context import MetaContext
from mlos.domain.models.meta_reasoning.meta_session import MetaSession
from mlos.domain.models.meta_reasoning.provider_capability import ProviderCapability
from mlos.domain.models.meta_reasoning.resource_allocation import ResourceAllocation
from mlos.domain.models.meta_reasoning.historical_evidence import HistoricalEvidence
from mlos.meta_reasoning.meta_planner import MetaPlanner
from mlos.domain.services.project_memory_service import ProjectMemoryService


class MetaService:
    """
    Coordinates context compilation, executes planning, and registers cognitive orchestrations.
    """

    def __init__(
        self,
        meta_planner: MetaPlanner,
        project_memory_service: ProjectMemoryService,
    ):
        self.meta_planner = meta_planner
        self.project_memory_service = project_memory_service

    def build_context(self, memory: ProjectMemory) -> MetaContext:
        """
        Translates ProjectMemory into an immutable MetaContext.
        """
        knowledge_summary = build_knowledge_summary(memory)

        # Default enterprise registry (local offline baseline and cloud targets)
        provider_registry = (
            ProviderCapability(
                provider_name="openai",
                model_name="gpt-4o",
                structured_output_support=True,
                reasoning_support=True,
                tool_calling=True,
                streaming=True,
                context_window=128000,
                latency_score=0.4,
                estimated_cost_per_1k_input=0.005,
                estimated_cost_per_1k_output=0.015,
                offline_availability=False,
            ),
            ProviderCapability(
                provider_name="anthropic",
                model_name="claude-3-5-sonnet",
                structured_output_support=True,
                reasoning_support=True,
                tool_calling=True,
                streaming=True,
                context_window=200000,
                latency_score=0.5,
                estimated_cost_per_1k_input=0.003,
                estimated_cost_per_1k_output=0.015,
                offline_availability=False,
            ),
            ProviderCapability(
                provider_name="google",
                model_name="gemini-1.5-pro",
                structured_output_support=True,
                reasoning_support=True,
                tool_calling=True,
                streaming=True,
                context_window=1000000,
                latency_score=0.6,
                estimated_cost_per_1k_input=0.00125,
                estimated_cost_per_1k_output=0.00375,
                offline_availability=False,
            ),
            ProviderCapability(
                provider_name="local",
                model_name="llama-3-8b",
                structured_output_support=True,
                reasoning_support=False,
                tool_calling=False,
                streaming=False,
                context_window=8000,
                latency_score=0.2,
                estimated_cost_per_1k_input=0.0,
                estimated_cost_per_1k_output=0.0,
                offline_availability=True,
            ),
        )

        user_constraints = ResourceAllocation(
            token_budget=100000,
            cost_budget_usd=1.0,
            cpu_cores_limit=2.0,
            memory_limit_mb=1024,
            cache_usage_limit_mb=50,
            max_worker_limits=1,
        )

        feedback_evidence = HistoricalEvidence(
            snapshots=tuple(memory.execution_snapshots),
            aggregated_accuracies={},
            proven_rules=(),
        )

        return MetaContext(
            project_name=memory.project_name,
            project_goal=memory.project_goal,
            dataset_summary=memory.dataset,
            feature_session=memory.feature_session,
            knowledge_summary=knowledge_summary,
            provider_registry=provider_registry,
            user_constraints=user_constraints,
            feedback_evidence=feedback_evidence,
            observed_at=datetime.utcnow(),
        )

    def orchestrate_cognition(self, memory: ProjectMemory) -> MetaSession:
        """
        Orchestrates planning configuration and registers the session.
        """
        context = self.build_context(memory)
        session = self.meta_planner.plan(context)

        # Persist session in memory
        self.project_memory_service.add_meta_session(memory, session)
        return session
