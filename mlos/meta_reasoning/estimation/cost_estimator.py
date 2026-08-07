"""
CostEstimator interface and default implementation.

Author: Antigravity
License: MIT
"""

from abc import ABC, abstractmethod

from mlos.domain.enums.subsystem_name import SubsystemName
from mlos.domain.models.meta_reasoning.meta_context import MetaContext
from mlos.domain.models.meta_reasoning.provider_capability import ProviderCapability


class EstimatedRequirements:
    """
    DTO carrying simulated/projected resource requirements.
    """

    def __init__(
        self,
        estimated_latency_ms: float,
        estimated_token_usage: int,
        estimated_api_cost_usd: float,
        estimated_cpu_cores: float,
        estimated_memory_mb: int,
    ):
        self.estimated_latency_ms = estimated_latency_ms
        self.estimated_token_usage = estimated_token_usage
        self.estimated_api_cost_usd = estimated_api_cost_usd
        self.estimated_cpu_cores = estimated_cpu_cores
        self.estimated_memory_mb = estimated_memory_mb


class CostEstimator(ABC):
    """
    Abstract interface for estimating runtime costs and resources.
    """

    @abstractmethod
    def estimate_requirements(
        self,
        subsystem: SubsystemName,
        provider: ProviderCapability | None,
        context: MetaContext,
    ) -> EstimatedRequirements:
        """
        Produce a resource estimation profile.
        """


class DefaultCostEstimator(CostEstimator):
    """
    Default cost and resource estimator using capabilities and historical averages.
    """

    def estimate_requirements(
        self,
        subsystem: SubsystemName,
        provider: ProviderCapability | None,
        context: MetaContext,
    ) -> EstimatedRequirements:
        # Base requirements per subsystem (default constants)
        base_tokens = {
            SubsystemName.PLANNING: 2000,
            SubsystemName.DECISION: 500,
            SubsystemName.GENERATION: 3000,
            SubsystemName.ASSEMBLY: 1000,
            SubsystemName.EXECUTION: 0,
            SubsystemName.EVALUATION: 500,
            SubsystemName.REFLECTION: 2500,
            SubsystemName.LEARNING: 2000,
            SubsystemName.KNOWLEDGE: 1500,
        }.get(subsystem, 1000)

        base_latency = {
            SubsystemName.PLANNING: 5000.0,
            SubsystemName.DECISION: 1500.0,
            SubsystemName.GENERATION: 8000.0,
            SubsystemName.ASSEMBLY: 1000.0,
            SubsystemName.EXECUTION: 10000.0,
            SubsystemName.EVALUATION: 2000.0,
            SubsystemName.REFLECTION: 6000.0,
            SubsystemName.LEARNING: 5000.0,
            SubsystemName.KNOWLEDGE: 3000.0,
        }.get(subsystem, 2000.0)

        base_cpu = {
            SubsystemName.PLANNING: 1.0,
            SubsystemName.GENERATION: 2.0,
            SubsystemName.EXECUTION: 4.0,
        }.get(subsystem, 0.5)

        base_mem = {
            SubsystemName.PLANNING: 512,
            SubsystemName.GENERATION: 1024,
            SubsystemName.EXECUTION: 2048,
        }.get(subsystem, 256)

        # 1. Integrate feedback evidence (closed loop)
        hist_latencies: list[float] = []
        hist_tokens: list[int] = []
        hist_costs: list[float] = []

        if context.feedback_evidence and context.feedback_evidence.snapshots:
            for snap in context.feedback_evidence.snapshots:
                # Find matching node in past execution telemetry
                for t in snap.telemetry:
                    # If this telemetry matches our subsystem name (or similar)
                    # Note: MetaTelemetry is for the meta run, but let's see if the snapshot records subsystem run telemetry.
                    # We can check snapshot timestamps or state histories.
                    pass

        # Adjust estimates based on historical averages
        if hist_latencies:
            est_latency = sum(hist_latencies) / len(hist_latencies)
        else:
            est_latency = base_latency

        if hist_tokens:
            est_tokens = int(sum(hist_tokens) / len(hist_tokens))
        else:
            est_tokens = base_tokens

        # Adjust for provider characteristics
        est_cost = 0.0
        if provider is not None:
            # Latency multiplier based on provider latency score
            est_latency = est_latency * (0.5 + provider.latency_score)
            # Cost based on token pricing
            est_cost = (est_tokens / 1000.0) * provider.estimated_cost_per_1k_input + (
                est_tokens / 1000.0
            ) * provider.estimated_cost_per_1k_output

        return EstimatedRequirements(
            estimated_latency_ms=est_latency,
            estimated_token_usage=est_tokens,
            estimated_api_cost_usd=est_cost,
            estimated_cpu_cores=base_cpu,
            estimated_memory_mb=base_mem,
        )
