"""
RankingProfile domain model.

Author: Antigravity
License: MIT
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RankingProfile:
    """
    Stores individual feature rankings by method along with the consensus rank.
    """

    mutual_information: tuple[str, ...] = field(default_factory=tuple)
    random_forest: tuple[str, ...] = field(default_factory=tuple)
    xgboost: tuple[str, ...] = field(default_factory=tuple)
    shap: tuple[str, ...] = field(default_factory=tuple)
    permutation_importance: tuple[str, ...] = field(default_factory=tuple)
    chi_square: tuple[str, ...] = field(default_factory=tuple)
    anova: tuple[str, ...] = field(default_factory=tuple)
    consensus_rrf: tuple[str, ...] = field(default_factory=tuple)
