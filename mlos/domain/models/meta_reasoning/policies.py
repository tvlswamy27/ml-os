"""
Policies sub-models.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CachePolicy:
    """
    Sub-policy controlling cache lookups and verification.
    """

    max_age_seconds: int
    force_refresh: bool
    cache_hit_action: str  # "USE_CACHE", "VALIDATE_CACHE", "BYPASS"


@dataclass(frozen=True)
class ValidationPolicy:
    """
    Sub-policy controlling output verification.
    """

    required_schemas: tuple[str, ...]
    fallback_on_failure: bool
    validation_mode: str  # "STRICT", "LAX"


@dataclass(frozen=True)
class RetryPolicy:
    """
    Sub-policy controlling recovery loop retry depths and backoff strategies.
    """

    max_retries: int
    backoff_factor: float
    fallback_strategy: str  # "FALLBACK_TO_RULE", "RAISE_ERROR", "DEFER"
