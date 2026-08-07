"""
ProviderSelectionStrategy abstraction and implementations.

Author: Antigravity
License: MIT
"""

from abc import ABC, abstractmethod

from mlos.domain.enums.subsystem_name import SubsystemName
from mlos.domain.models.meta_reasoning.meta_context import MetaContext
from mlos.domain.models.meta_reasoning.provider_capability import ProviderCapability


class ProviderSelectionStrategy(ABC):
    """
    Abstract interface for selecting the optimal provider/model capability.
    """

    @abstractmethod
    def select_provider(
        self, subsystem: SubsystemName, context: MetaContext
    ) -> ProviderCapability | None:
        """
        Selects a provider capability based on context and subsystem characteristics.
        """


class RuleProviderSelector(ProviderSelectionStrategy):
    """
    Selects provider based on simple heuristics or manual configuration.
    """

    def select_provider(
        self, subsystem: SubsystemName, context: MetaContext
    ) -> ProviderCapability | None:
        if not context.provider_registry:
            return None
        # Default: pick first matching local/offline model if constraints require it
        if (
            context.user_constraints.additional_resources.get(
                "must_use_local_models", 0.0
            )
            > 0.0
        ):
            for p in context.provider_registry:
                if p.offline_availability:
                    return p
        return context.provider_registry[0]


class CapabilityProviderSelector(ProviderSelectionStrategy):
    """
    Selects a provider that strictly satisfies all requested capability flags.
    """

    def select_provider(
        self, subsystem: SubsystemName, context: MetaContext
    ) -> ProviderCapability | None:
        if not context.provider_registry:
            return None

        # Determine capabilities required for the subsystem
        need_structured = subsystem in (
            SubsystemName.PLANNING,
            SubsystemName.DECISION,
            SubsystemName.GENERATION,
            SubsystemName.REFLECTION,
            SubsystemName.LEARNING,
            SubsystemName.KNOWLEDGE,
        )
        need_reasoning = subsystem in (SubsystemName.PLANNING, SubsystemName.REFLECTION)
        need_tools = subsystem in (SubsystemName.GENERATION, SubsystemName.ASSEMBLY)

        candidates = list(context.provider_registry)

        # Filters
        if need_structured:
            candidates = [c for c in candidates if c.structured_output_support]
        if need_reasoning:
            candidates = [c for c in candidates if c.reasoning_support]
        if need_tools:
            candidates = [c for c in candidates if c.tool_calling]

        # Filter by constraints
        if (
            context.user_constraints.additional_resources.get(
                "must_use_local_models", 0.0
            )
            > 0.0
        ):
            candidates = [c for c in candidates if c.offline_availability]

        if not candidates:
            # Fallback to rule selector if no perfect match
            return RuleProviderSelector().select_provider(subsystem, context)

        return candidates[0]


class CostAwareProviderSelector(ProviderSelectionStrategy):
    """
    Selects the cheapest provider capability that meets offline and general criteria.
    """

    def select_provider(
        self, subsystem: SubsystemName, context: MetaContext
    ) -> ProviderCapability | None:
        if not context.provider_registry:
            return None

        candidates = list(context.provider_registry)
        if (
            context.user_constraints.additional_resources.get(
                "must_use_local_models", 0.0
            )
            > 0.0
        ):
            candidates = [c for c in candidates if c.offline_availability]

        if not candidates:
            return None

        # Sort by estimated cost per 1k input tokens (as a proxy)
        candidates.sort(key=lambda x: x.estimated_cost_per_1k_input)
        return candidates[0]


class LatencyAwareProviderSelector(ProviderSelectionStrategy):
    """
    Selects the provider with the lowest latency score.
    """

    def select_provider(
        self, subsystem: SubsystemName, context: MetaContext
    ) -> ProviderCapability | None:
        if not context.provider_registry:
            return None

        candidates = list(context.provider_registry)
        if (
            context.user_constraints.additional_resources.get(
                "must_use_local_models", 0.0
            )
            > 0.0
        ):
            candidates = [c for c in candidates if c.offline_availability]

        if not candidates:
            return None

        candidates.sort(key=lambda x: x.latency_score)
        return candidates[0]


class HybridProviderSelector(ProviderSelectionStrategy):
    """
    Selects a provider balancing cost and latency capabilities.
    """

    def select_provider(
        self, subsystem: SubsystemName, context: MetaContext
    ) -> ProviderCapability | None:
        if not context.provider_registry:
            return None

        candidates = list(context.provider_registry)
        if (
            context.user_constraints.additional_resources.get(
                "must_use_local_models", 0.0
            )
            > 0.0
        ):
            candidates = [c for c in candidates if c.offline_availability]

        if not candidates:
            return None

        # Combine cost and latency score normalized: cost * 0.5 + latency * 0.5
        candidates.sort(
            key=lambda x: (x.estimated_cost_per_1k_input * 100.0) * 0.5
            + x.latency_score * 0.5
        )
        return candidates[0]
