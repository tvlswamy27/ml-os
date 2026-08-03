"""
ProviderCapability domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCapability:
    """
    Immutable specification of provider capability features.
    """

    provider_name: str
    model_name: str
    structured_output_support: bool
    reasoning_support: bool
    tool_calling: bool
    streaming: bool
    context_window: int
    latency_score: float  # Scale 0.0 to 1.0
    estimated_cost_per_1k_input: float
    estimated_cost_per_1k_output: float
    offline_availability: bool
