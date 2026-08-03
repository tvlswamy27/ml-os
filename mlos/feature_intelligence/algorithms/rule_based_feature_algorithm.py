"""
RuleBasedFeatureAlgorithm implementation.

Author: Antigravity
License: MIT
"""

import math
import numpy as np
import pandas as pd
from datetime import datetime
from mlos.feature_intelligence.algorithms.feature_algorithm import FeatureAlgorithm
from mlos.domain.models.feature_intelligence import (
    FeatureContext,
    FeatureSession,
    FeatureReasoningState,
    FeatureStatistics,
    FeatureQualityScore,
    FeatureProfile,
    FeatureLineage,
    FeatureEngineeringProposal,
    FeatureInsight,
    FeatureNode,
    FeatureEdge,
    FeatureGraph,
    RankingProfile,
    RelationshipProfile,
    RecommendationEvidence,
    FeatureRecommendation,
    FeatureConfidence,
)
from mlos.domain.enums.feature_type import FeatureType
from mlos.domain.enums.recommendation_action import RecommendationAction
from mlos.feature_intelligence.algorithms.ranking import (
    MutualInformationRankingStrategy,
    RandomForestRankingStrategy,
    XGBoostRankingStrategy,
    ShapRankingStrategy,
    PermutationImportanceRankingStrategy,
    AnovaRankingStrategy,
    ChiSquareRankingStrategy,
)


class RuleBasedFeatureAlgorithm(FeatureAlgorithm):
    """
    Deterministic rule-based feature intelligence algorithm.
    """

    def __init__(self, ranking_strategies=None):
        """
        Initialize with standard pluggable ranking strategies.
        """
        if ranking_strategies is None:
            self.ranking_strategies = [
                AnovaRankingStrategy(),
                ChiSquareRankingStrategy(),
                MutualInformationRankingStrategy(),
                RandomForestRankingStrategy(),
                XGBoostRankingStrategy(),
                ShapRankingStrategy(),
                PermutationImportanceRankingStrategy(),
            ]
        else:
            self.ranking_strategies = ranking_strategies

    def can_analyze(self, context: FeatureContext) -> bool:
        """
        Always returns True to serve as the baseline rule-based feature analyzer.
        """
        return True

    def _discover_features(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> None:
        """
        Discover type-safe feature categories, target leakages, and identifiers.
        """
        discovered_types = {}
        target = context.dataset.target if context.dataset else None
        target_leakages = []

        for col in dataframe.columns:
            # Check for identifiers
            col_lower = col.lower()
            is_id = False
            if (
                col_lower.endswith("id")
                or col_lower.startswith("id_")
                or col_lower == "id"
                or col_lower == "uuid"
                or col_lower.endswith("key")
            ):
                is_id = True

            # DataType logic
            dtype = dataframe[col].dtype
            if is_id:
                discovered_types[col] = FeatureType.IDENTIFIER
            elif col_lower in ("lat", "latitude", "lon", "longitude", "lng", "geohash"):
                discovered_types[col] = FeatureType.GEOSPATIAL
            elif pd.api.types.is_bool_dtype(dtype):
                discovered_types[col] = FeatureType.BOOLEAN
            elif (
                pd.api.types.is_datetime64_any_dtype(dtype)
                or "date" in col_lower
                or "time" in col_lower
            ):
                discovered_types[col] = FeatureType.DATETIME
            elif pd.api.types.is_numeric_dtype(dtype):
                # Check if it behaves as a Boolean (only 0 and 1 or single value)
                unique_vals = dataframe[col].dropna().unique()
                if len(unique_vals) <= 2 and set(unique_vals).issubset(
                    {0, 1, 0.0, 1.0, True, False}
                ):
                    discovered_types[col] = FeatureType.BOOLEAN
                else:
                    discovered_types[col] = FeatureType.NUMERIC
            elif pd.api.types.is_string_dtype(dtype) or pd.api.types.is_object_dtype(
                dtype
            ):
                unique_count = dataframe[col].nunique()
                # Check for booleans in object columns
                unique_vals = set(
                    dataframe[col].dropna().astype(str).str.lower().unique()
                )
                if unique_vals.issubset(
                    {"true", "false", "t", "f", "yes", "no", "y", "n"}
                ):
                    discovered_types[col] = FeatureType.BOOLEAN
                elif unique_count < 20:
                    discovered_types[col] = FeatureType.CATEGORICAL
                else:
                    # Heuristic for free text vs high cardinality categories
                    avg_len = dataframe[col].astype(str).str.len().mean()
                    if avg_len > 50:
                        discovered_types[col] = FeatureType.TEXT
                    else:
                        discovered_types[col] = FeatureType.CATEGORICAL
            else:
                discovered_types[col] = FeatureType.UNKNOWN

            # Target leakage check: name similarity or direct copy
            if target and col != target:
                if (
                    col_lower == f"{target.lower()}_copy"
                    or col_lower == f"target_{target.lower()}"
                ):
                    target_leakages.append(col)
                # Check if it has 100% correlation
                if pd.api.types.is_numeric_dtype(
                    dataframe[col].dtype
                ) and pd.api.types.is_numeric_dtype(dataframe[target].dtype):
                    try:
                        corr = dataframe[col].corr(dataframe[target])
                        if pd.notna(corr) and abs(corr) >= 0.999:
                            target_leakages.append(col)
                    except Exception:
                        pass

        # Write facts
        state.facts["discovered_columns"] = ",".join(dataframe.columns)
        object.__setattr__(state, "target_leakage_candidates", tuple(target_leakages))

        # Store intermediate mapping in facts for downstream stage access
        for col, ftype in discovered_types.items():
            state.facts[f"type_{col}"] = ftype.value

    def _profile_features(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> None:
        """
        Compute FeatureStatistics and build FeatureProfile structures.
        """
        profiles = {}
        total_rows = len(dataframe)

        for col in dataframe.columns:
            # Calculate stats
            missing_count = int(dataframe[col].isna().sum())
            missing_pct = float(missing_count / total_rows) if total_rows > 0 else 0.0

            unique_count = int(dataframe[col].nunique())
            uniqueness_ratio = (
                float(unique_count / total_rows) if total_rows > 0 else 0.0
            )

            # Calculate duplicate ratio
            try:
                dup_ratio = (
                    float(dataframe[col].duplicated().sum() / total_rows)
                    if total_rows > 0
                    else 0.0
                )
            except Exception:
                dup_ratio = 0.0

            # Entropy calculation
            entropy_val = 0.0
            try:
                counts = dataframe[col].dropna().value_counts()
                if not counts.empty:
                    probs = counts / counts.sum()
                    entropy_val = float(-np.sum(probs * np.log2(probs)))
            except Exception:
                pass

            # Numeric statistics
            variance_val = 0.0
            skewness_val = 0.0
            kurtosis_val = 0.0
            outlier_pct = 0.0

            ftype_str = state.facts.get(f"type_{col}", FeatureType.UNKNOWN.value)
            ftype = FeatureType(ftype_str)

            if ftype == FeatureType.NUMERIC:
                try:
                    variance_val = float(dataframe[col].var())
                    skewness_val = float(dataframe[col].skew())
                    kurtosis_val = float(dataframe[col].kurt())

                    # Outliers detection using IQR
                    q1 = dataframe[col].quantile(0.25)
                    q3 = dataframe[col].quantile(0.75)
                    iqr = q3 - q1
                    if iqr > 0:
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr
                        outliers = dataframe[
                            (dataframe[col] < lower_bound)
                            | (dataframe[col] > upper_bound)
                        ]
                        outlier_pct = float(len(outliers) / total_rows)
                except Exception:
                    pass

            stats = FeatureStatistics(
                missing_percentage=missing_pct,
                variance=variance_val if pd.notna(variance_val) else 0.0,
                skewness=skewness_val if pd.notna(skewness_val) else 0.0,
                kurtosis=kurtosis_val if pd.notna(kurtosis_val) else 0.0,
                entropy=entropy_val if pd.notna(entropy_val) else 0.0,
                uniqueness_ratio=uniqueness_ratio,
                duplicate_ratio=dup_ratio,
                outlier_percentage=outlier_pct,
            )

            # Feature Quality Score logic
            info_score = (
                min(1.0, max(0.0, entropy_val / 10.0)) if entropy_val > 0 else 0.0
            )
            stability_score = max(0.0, 1.0 - (missing_pct + outlier_pct))

            # Simple heuristic redundancy metric
            redundancy_val = 0.0

            overall_score = float(
                0.4 * info_score + 0.4 * stability_score + 0.2 * (1.0 - redundancy_val)
            )

            confidence = FeatureConfidence(
                score=0.9,
                uncertainty=0.1,
                supporting_evidence=("missing_percentage", "variance"),
                explanation="Rule-based heuristic quality scoring profile.",
            )

            quality = FeatureQualityScore(
                overall_score=overall_score,
                information_score=info_score,
                stability_score=stability_score,
                redundancy_score=1.0 - redundancy_val,
                engineering_potential=(
                    0.5 if missing_pct > 0.05 or abs(skewness_val) > 1.5 else 0.1
                ),
                confidence=confidence,
            )

            is_constant = variance_val == 0.0 and ftype == FeatureType.NUMERIC
            is_dup = dup_ratio >= 0.99
            is_identifier = ftype == FeatureType.IDENTIFIER

            profiles[col] = FeatureProfile(
                column_name=col,
                feature_type=ftype,
                statistics=stats,
                quality_score=quality,
                is_constant=is_constant,
                is_duplicate=is_dup,
                is_identifier=is_identifier,
                cardinality=unique_count,
            )

        object.__setattr__(state, "feature_profiles", profiles)

    def _analyze_relationships(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> None:
        """
        Compute Pearson/Spearman correlations, Cramer's V, VIF, and construct the FeatureGraph.
        """
        pearson_mat: dict[str, dict[str, float]] = {}
        spearman_mat: dict[str, dict[str, float]] = {}
        vif_scores: dict[str, float] = {}
        target_corr: dict[str, float] = {}
        redundant_groups: list[tuple[str, ...]] = []

        target = context.dataset.target if context.dataset else None

        # Pearson and Spearman for numeric features
        num_cols = [
            col
            for col, prof in state.feature_profiles.items()
            if prof.feature_type == FeatureType.NUMERIC
        ]
        if len(num_cols) > 1:
            try:
                p_df = dataframe[num_cols].corr(method="pearson").fillna(0.0)
                s_df = dataframe[num_cols].corr(method="spearman").fillna(0.0)

                for c1 in num_cols:
                    pearson_mat[c1] = {}
                    spearman_mat[c1] = {}
                    for c2 in num_cols:
                        pearson_mat[c1][c2] = float(p_df.loc[c1, c2])
                        spearman_mat[c1][c2] = float(s_df.loc[c1, c2])
            except Exception:
                pass

        # Target correlations
        if target and target in dataframe.columns:
            for col in num_cols:
                if col != target:
                    try:
                        corr = float(dataframe[col].corr(dataframe[target]))
                        target_corr[col] = corr if pd.notna(corr) else 0.0
                    except Exception:
                        target_corr[col] = 0.0

        # Calculate VIF for numeric features
        if len(num_cols) > 2:
            try:
                from sklearn.linear_model import LinearRegression

                for col in num_cols:
                    predictors = [c for c in num_cols if c != col]
                    df_clean = dataframe[[col] + predictors].dropna()
                    if len(df_clean) > 10:
                        X = df_clean[predictors]
                        y = df_clean[col]
                        reg = LinearRegression().fit(X, y)
                        r2 = reg.score(X, y)
                        vif = 1.0 / (1.0 - r2) if r2 < 1.0 else float("inf")
                        vif_scores[col] = float(vif)
            except Exception:
                pass

        # Detect redundant groups (correlation >= 0.85)
        visited = set()
        for col1 in num_cols:
            if col1 in visited:
                continue
            corr_group = [col1]
            for col2 in num_cols:
                if col1 != col2:
                    p_corr = pearson_mat.get(col1, {}).get(col2, 0.0)
                    if abs(p_corr) >= 0.85:
                        corr_group.append(col2)
                        visited.add(col2)
            if len(corr_group) > 1:
                redundant_groups.append(tuple(corr_group))

        # Build FeatureGraph nodes and edges
        nodes = {}
        edges = []
        for col, prof in state.feature_profiles.items():
            nodes[col] = FeatureNode(column_name=col, feature_type=prof.feature_type)

        # Correlation edges in graph
        for c1, target_dict in pearson_mat.items():
            for c2, val in target_dict.items():
                if c1 < c2 and abs(val) >= 0.5:
                    edges.append(
                        FeatureEdge(
                            source=c1,
                            target=c2,
                            edge_type="correlation",
                            properties={"pearson": val},
                        )
                    )

        # Redundancy edges in graph
        for group in redundant_groups:
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    edges.append(
                        FeatureEdge(
                            source=group[i],
                            target=group[j],
                            edge_type="redundancy",
                            properties={"threshold": 0.85},
                        )
                    )

        graph = FeatureGraph(nodes=nodes, edges=edges)
        rel_profile = RelationshipProfile(
            graph=graph,
            pearson_matrix=pearson_mat,
            spearman_matrix=spearman_mat,
            vif_scores=vif_scores,
            target_correlation=target_corr,
            redundant_feature_groups=tuple(redundant_groups),
        )
        object.__setattr__(state, "relationship_profile", rel_profile)

    def _generate_insights(
        self,
        context: FeatureContext,
        state: FeatureReasoningState,
    ) -> list[FeatureInsight]:
        """
        Generate FeatureInsight warnings/observations from the reasoning state.
        """
        insights = []
        idx = 0

        # Target leakages
        for col in state.target_leakage_candidates:
            insights.append(
                FeatureInsight(
                    insight_id=f"INSIGHT-{idx:03d}",
                    insight_type="TARGET_LEAKAGE",
                    severity="CRITICAL",
                    summary=f"Column '{col}' exhibits target leakage.",
                    affected_columns=(col,),
                    explanation="This column has nearly 100% correlation or identical name matching with the target.",
                )
            )
            idx += 1

        # High missingness
        for col, prof in state.feature_profiles.items():
            missing_pct = prof.statistics.missing_percentage
            if missing_pct >= 0.5:
                insights.append(
                    FeatureInsight(
                        insight_id=f"INSIGHT-{idx:03d}",
                        insight_type="HIGH_MISSING",
                        severity="HIGH" if missing_pct < 0.8 else "CRITICAL",
                        summary=f"Feature '{col}' has {missing_pct:.1%} missing values.",
                        affected_columns=(col,),
                        value=missing_pct,
                        explanation="High missing rates reduce modeling strength and require removal or heavy imputation.",
                    )
                )
                idx += 1

        # Multicollinearity
        for col, vif in state.relationship_profile.vif_scores.items():
            if vif > 10.0:
                insights.append(
                    FeatureInsight(
                        insight_id=f"INSIGHT-{idx:03d}",
                        insight_type="MULTICOLLINEARITY",
                        severity="MEDIUM" if vif < 30.0 else "HIGH",
                        summary=f"Feature '{col}' shows high multicollinearity (VIF: {vif:.1f}).",
                        affected_columns=(col,),
                        value=vif,
                        explanation="High VIF scores suggest feature redundancy which can destablize linear modeling coefficients.",
                    )
                )
                idx += 1

        # High Skewness
        for col, prof in state.feature_profiles.items():
            skew = prof.statistics.skewness
            if abs(skew) >= 2.0:
                insights.append(
                    FeatureInsight(
                        insight_id=f"INSIGHT-{idx:03d}",
                        insight_type="HIGH_SKEWNESS",
                        severity="LOW",
                        summary=f"Feature '{col}' is highly skewed (skew: {skew:.2f}).",
                        affected_columns=(col,),
                        value=skew,
                        explanation="Highly skewed predictors benefit from mathematical transformations (e.g., log, box-cox).",
                    )
                )
                idx += 1

        return insights

    def _rank_features(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> RankingProfile:
        """
        Evaluate individual ranking strategies, store outputs, and build a consensus RRF rank.
        """
        raw_rankings = {}
        for strategy in self.ranking_strategies:
            try:
                scores = strategy.score_features(context, dataframe, state)
                # Sort features by score descending
                sorted_features = sorted(
                    scores.keys(), key=lambda k: scores[k], reverse=True
                )
                raw_rankings[strategy.name] = tuple(sorted_features)
            except Exception:
                raw_rankings[strategy.name] = ()

        # Consensus ranking via Reciprocal Rank Fusion (RRF)
        # RRF(f) = sum_m ( 1 / (60 + rank_m(f)) )
        rrf_scores = {}
        k = 60
        all_features = set(dataframe.columns)
        if context.dataset and context.dataset.target:
            all_features.discard(context.dataset.target)

        for col in all_features:
            score = 0.0
            for name, rank_tuple in raw_rankings.items():
                if col in rank_tuple:
                    # rank is 1-indexed
                    rank = rank_tuple.index(col) + 1
                    score += 1.0 / (k + rank)
            rrf_scores[col] = score

        consensus_rank = tuple(
            sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)
        )

        ranking_profile = RankingProfile(
            mutual_information=raw_rankings.get("mutual_information", ()),
            random_forest=raw_rankings.get("random_forest", ()),
            xgboost=raw_rankings.get("xgboost", ()),
            shap=raw_rankings.get("shap", ()),
            permutation_importance=raw_rankings.get("permutation_importance", ()),
            chi_square=raw_rankings.get("chi_square", ()),
            anova=raw_rankings.get("anova", ()),
            consensus_rrf=consensus_rank,
        )

        object.__setattr__(state, "ranking_profile", ranking_profile)
        return ranking_profile

    def _recommend_engineering(
        self,
        context: FeatureContext,
        dataframe: pd.DataFrame,
        state: FeatureReasoningState,
    ) -> list[FeatureEngineeringProposal]:
        """
        Generate feature engineering proposals based on profile characteristics.
        """
        proposals = []
        idx = 0

        # Log transform for highly skewed features
        for col, prof in state.feature_profiles.items():
            if (
                prof.feature_type == FeatureType.NUMERIC
                and abs(prof.statistics.skewness) >= 1.5
            ):
                # Confirm all values are non-negative for standard log
                try:
                    min_val = dataframe[col].min()
                except Exception:
                    min_val = 0.0

                suffix = "_log" if min_val > 0 else "_log1p"
                transformation = "log" if min_val > 0 else "log1p"

                confidence = FeatureConfidence(
                    score=0.85,
                    uncertainty=0.15,
                    supporting_evidence=(f"skewness_{prof.statistics.skewness:.2f}",),
                    explanation=f"Skewed variable '{col}' warrants a non-linear transform to stabilize variance.",
                )
                lineage = FeatureLineage(
                    parent_features=(col,),
                    transformation=transformation,
                    generation_step=1,
                )
                proposals.append(
                    FeatureEngineeringProposal(
                        proposal_id=f"ENG-{idx:03d}",
                        source_columns=(col,),
                        generated_feature=f"{col}{suffix}",
                        transformation=transformation,
                        expected_gain=0.05,
                        computational_cost="LOW",
                        confidence=confidence,
                        lineage=lineage,
                    )
                )
                idx += 1

        # Date part extractions for datetime features
        for col, prof in state.feature_profiles.items():
            if prof.feature_type == FeatureType.DATETIME:
                confidence = FeatureConfidence(
                    score=0.9,
                    uncertainty=0.1,
                    supporting_evidence=("datetime_type",),
                    explanation="Dates are best processed by extracting temporal parts.",
                )
                lineage = FeatureLineage(
                    parent_features=(col,),
                    transformation="extract_date_parts",
                    generation_step=1,
                )
                proposals.append(
                    FeatureEngineeringProposal(
                        proposal_id=f"ENG-{idx:03d}",
                        source_columns=(col,),
                        generated_feature=f"{col}_year",
                        transformation="extract_year",
                        expected_gain=0.1,
                        computational_cost="LOW",
                        confidence=confidence,
                        lineage=lineage,
                    )
                )
                idx += 1

        return proposals

    def _select_features(
        self,
        context: FeatureContext,
        ranking: RankingProfile,
        state: FeatureReasoningState,
    ) -> list[FeatureRecommendation]:
        """
        Formulate selection recommendations (KEEP, REMOVE, TRANSFORM, ENGINEER, MERGE).
        """
        recommendations = []
        idx = 0

        target = context.dataset.target if context.dataset else None

        for col, prof in state.feature_profiles.items():
            if target and col == target:
                continue

            # Default: KEEP
            action = RecommendationAction.KEEP
            reason = "Feature exhibits standard statistical properties."
            score = 1.0
            uncertainty = 0.0
            rules = []
            stats_used = []
            thresholds = {}

            # Target Leakage rule
            if col in state.target_leakage_candidates:
                action = RecommendationAction.REMOVE
                reason = "Potential target leakage; contains predictive information not available at runtime."
                score = 0.99
                rules = ["target_leakage_prevention"]
                stats_used = ["correlation"]

            # Constant Column rule
            elif prof.is_constant:
                action = RecommendationAction.REMOVE
                reason = "Zero variance column; carries no information."
                score = 0.99
                rules = ["constant_column_filter"]
                stats_used = ["variance"]
                thresholds = {"variance_limit": 0.0}

            # Extremely high missing rule
            elif prof.statistics.missing_percentage >= 0.8:
                action = RecommendationAction.REMOVE
                reason = "Extremely high missing percentage; exceeding imputable range."
                score = 0.95
                rules = ["missingness_bound"]
                stats_used = ["missing_percentage"]
                thresholds = {"missing_limit": 0.8}

            # Categorical Encoding recommendation
            elif prof.feature_type == FeatureType.CATEGORICAL:
                action = RecommendationAction.TRANSFORM
                reason = "Categorical variable needs encoding (One-Hot or Label)."
                score = 0.9
                rules = ["categorical_encoding_rule"]
                stats_used = ["cardinality"]

            evidence = RecommendationEvidence(
                triggered_rules=tuple(rules),
                statistics_used=tuple(stats_used),
                thresholds=thresholds,
                supporting_features=(col,),
                notes=(),
            )

            confidence = FeatureConfidence(
                score=score,
                uncertainty=uncertainty,
                supporting_evidence=tuple(stats_used),
                explanation=reason,
            )

            recommendations.append(
                FeatureRecommendation(
                    recommendation_id=f"REC-{idx:03d}",
                    action=action,
                    target_columns=(col,),
                    reasoning=reason,
                    confidence=confidence,
                    evidence=evidence,
                )
            )
            idx += 1

        return recommendations

    def _construct_session(
        self,
        context: FeatureContext,
        state: FeatureReasoningState,
        insights: list[FeatureInsight],
        recommendations: list[FeatureRecommendation],
        proposals: list[FeatureEngineeringProposal],
        ranking_profile: RankingProfile,
    ) -> FeatureSession:
        """
        Assemble and construct the final immutable FeatureSession.
        """
        return FeatureSession(
            context=context,
            reasoning_state=state,
            insights=insights,
            recommendations=recommendations,
            engineering_proposals=proposals,
            consensus_ranking=ranking_profile.consensus_rrf,
            status="SUCCESS",
        )
