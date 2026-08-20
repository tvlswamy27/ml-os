"""
CLI Persistence helper.

Responsible for saving and loading lightweight project configurations.

Author: Vikram Tanakala
License: MIT
"""

import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from mlos.domain.enums.execution_lifecycle import ExecutionLifecycle
from mlos.domain.enums.execution_mode import ExecutionMode
from mlos.domain.enums.feature_type import FeatureType
from mlos.domain.enums.recommendation_action import RecommendationAction
from mlos.domain.enums.subsystem_name import SubsystemName
from mlos.domain.models.feature_intelligence import (
    FeatureConfidence,
    FeatureContext,
    FeatureEdge,
    FeatureEngineeringProposal,
    FeatureGraph,
    FeatureInsight,
    FeatureLineage,
    FeatureNode,
    FeatureProfile,
    FeatureQualityScore,
    FeatureReasoningState,
    FeatureRecommendation,
    FeatureSession,
    FeatureStatistics,
    RankingProfile,
    RecommendationEvidence,
    RelationshipProfile,
)
from mlos.domain.models.meta_reasoning import (
    CachePolicy,
    DecisionEvidence,
    DecisionRule,
    DecisionTrace,
    ExecutionPlan,
    ExecutionPolicy,
    ExecutionSchedule,
    ExecutionSnapshot,
    ExecutionStrategy,
    HistoricalEvidence,
    MetaContext,
    MetaReasoningState,
    MetaSession,
    PolicyVersion,
    ProviderCapability,
    ResourceAllocation,
    RetryPolicy,
    ScheduleDependency,
    ScheduleNode,
    ValidationPolicy,
)
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.services.project_memory_service import ProjectMemoryService

if TYPE_CHECKING:
    from mlos.domain.models.knowledge.knowledge_entry import KnowledgeEntry
    from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession
    from mlos.domain.models.learning.learning_session import LearningSession
    from mlos.domain.models.reflection.reflection_session import ReflectionSession


def find_project_root(start_dir: Path | str | None = None) -> Path | None:
    """
    Search order for active ML-OS project root:
    1. Current directory (start_dir)
    2. Parent directories up to filesystem root
    3. Immediate child directories of start_dir
    """
    if start_dir:
        current = Path(start_dir).resolve()
    else:
        current = Path(os.getcwd()).resolve()

    # 1 & 2: Search current directory and parent directories
    for parent in [current] + list(current.parents):
        if (parent / ".mlos").is_dir() and str(parent.resolve()).lower() != str(Path.home().resolve()).lower():
            return parent

    # 3: Search immediate child directories
    if current.is_dir():
        try:
            subdirs = [
                d for d in current.iterdir() if d.is_dir() and (d / ".mlos").is_dir() and str(d.resolve()).lower() != str(Path.home().resolve()).lower()
            ]
            if subdirs:
                return subdirs[0]
        except Exception:
            pass

    return None


def load_project_config(project_root: Path) -> dict | None:
    """
    Load project configurations from the project's .mlos directory.
    """
    config_file = project_root / ".mlos" / "project_config.yaml"
    if not config_file.is_file():
        return None
    with open(config_file, "r") as f:
        return yaml.safe_load(f) or {}


def save_project_config(project_root: Path, config: dict) -> None:
    """
    Save project configurations to the project's .mlos directory.
    """
    config_file = project_root / ".mlos" / "project_config.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False)


def reconstruct_project_memory(project_root: Path) -> ProjectMemory | None:
    """
    Reconstruct ProjectMemory from the lightweight config on disk.
    """
    config_file = project_root / ".mlos" / "project_config.yaml"
    if not config_file.is_file():
        return None
    with open(config_file, "r") as f:
        content = f.read()

    from mlos.serialization import serialization_engine
    from mlos.serialization.version import SchemaVersion

    try:
        memory = serialization_engine.deserialize(
            content, ProjectMemory, target_version=SchemaVersion(3, 0, 0), format="yaml"
        )
        return memory
    except Exception:
        # Fallback to legacy reconstruct for older configs or untagged configs
        pass

    config = load_project_config(project_root)
    if config is None:
        return None

    memory_service = ProjectMemoryService()
    memory = memory_service.create(
        project_name=config.get("project_name", ""),
        project_goal=config.get("project_goal", ""),
    )

    if "current_stage" in config:
        memory.current_stage = config["current_stage"]
    if "completed_tasks" in config:
        memory.completed_tasks = config.get("completed_tasks", [])
    if "notes" in config:
        memory.notes = config.get("notes", [])

    dataset_path = config.get("dataset_path")
    if dataset_path:
        from mlos.domain.models.dataset import Dataset

        dataset = Dataset(
            path=dataset_path,
            target=config.get("target_column"),
        )
        memory.dataset = dataset

    if "reflection_sessions" in config:
        memory.reflection_sessions = [
            dict_to_reflection_session(s) for s in config["reflection_sessions"]
        ]

    if "learning_sessions" in config:
        memory.learning_sessions = [
            dict_to_learning_session(s) for s in config["learning_sessions"]
        ]

    if "knowledge_sessions" in config:
        memory.knowledge_sessions = [
            dict_to_knowledge_session(s) for s in config["knowledge_sessions"]
        ]

    if "knowledge_entries" in config:
        memory.knowledge_entries = [
            dict_to_knowledge_entry(e) for e in config["knowledge_entries"]
        ]

    if "feature_sessions" in config:
        memory.feature_sessions = [
            dict_to_feature_session(s) for s in config["feature_sessions"]
        ]

    if "meta_sessions" in config:
        memory.meta_sessions = [
            dict_to_meta_session(s) for s in config["meta_sessions"]
        ]

    if "execution_snapshots" in config:
        memory.execution_snapshots = [
            dict_to_execution_snapshot(s) for s in config["execution_snapshots"]
        ]

    return memory


def dict_to_feature_session(data: dict) -> FeatureSession:
    """Helper to reconstruct a FeatureSession from raw dict."""
    from datetime import datetime
    from uuid import UUID

    from mlos.domain.models.dataset import Dataset
    from mlos.domain.models.knowledge_summary import KnowledgeSummary

    c_data = data.get("context", {})
    dataset = None
    ds_data = c_data.get("dataset")
    if ds_data:
        dataset = Dataset(
            path=ds_data.get("path", ""),
            rows=ds_data.get("rows", 0),
            columns=ds_data.get("columns", 0),
            target=ds_data.get("target"),
            problem_type=ds_data.get("problem_type"),
            categorical_columns=list(ds_data.get("categorical_columns", [])),
            numerical_columns=list(ds_data.get("numerical_columns", [])),
            missing_values=dict(ds_data.get("missing_values", {})),
            duplicate_rows=ds_data.get("duplicate_rows", 0),
            unique_values=dict(ds_data.get("unique_values", {})),
            missing_percentages=dict(ds_data.get("missing_percentages", {})),
            column_types=dict(ds_data.get("column_types", {})),
        )

    context = FeatureContext(
        project_name=c_data.get("project_name", ""),
        project_goal=c_data.get("project_goal", ""),
        dataset=dataset,
        knowledge_summary=KnowledgeSummary(),  # Can reconstruct active knowledge from memory elsewhere
        observed_at=(
            datetime.fromisoformat(c_data["observed_at"])
            if "observed_at" in c_data
            else datetime.now()
        ),
    )

    rs_data = data.get("reasoning_state", {})
    profiles = {}
    for col, p in rs_data.get("feature_profiles", {}).items():
        stats_data = p.get("statistics", {})
        stats = FeatureStatistics(
            missing_percentage=stats_data.get("missing_percentage", 0.0),
            variance=stats_data.get("variance", 0.0),
            skewness=stats_data.get("skewness", 0.0),
            kurtosis=stats_data.get("kurtosis", 0.0),
            entropy=stats_data.get("entropy", 0.0),
            uniqueness_ratio=stats_data.get("uniqueness_ratio", 0.0),
            duplicate_ratio=stats_data.get("duplicate_ratio", 0.0),
            outlier_percentage=stats_data.get("outlier_percentage", 0.0),
        )

        qs_data = p.get("quality_score", {})
        conf_data = qs_data.get("confidence", {})
        confidence = FeatureConfidence(
            score=conf_data.get("score", 1.0),
            uncertainty=conf_data.get("uncertainty", 0.0),
            supporting_evidence=tuple(conf_data.get("supporting_evidence", ())),
            explanation=conf_data.get("explanation", ""),
        )

        quality = FeatureQualityScore(
            overall_score=qs_data.get("overall_score", 1.0),
            information_score=qs_data.get("information_score", 1.0),
            stability_score=qs_data.get("stability_score", 1.0),
            redundancy_score=qs_data.get("redundancy_score", 1.0),
            engineering_potential=qs_data.get("engineering_potential", 0.0),
            confidence=confidence,
        )

        profiles[col] = FeatureProfile(
            column_name=p.get("column_name", col),
            feature_type=FeatureType(p.get("feature_type", "unknown")),
            statistics=stats,
            quality_score=quality,
            is_constant=p.get("is_constant", False),
            is_duplicate=p.get("is_duplicate", False),
            is_identifier=p.get("is_identifier", False),
            cardinality=p.get("cardinality", 0),
        )

    rel_data = rs_data.get("relationship_profile", {})
    g_data = rel_data.get("graph", {})
    nodes = {}
    for k, v in g_data.get("nodes", {}).items():
        nodes[k] = FeatureNode(
            column_name=v.get("column_name", k),
            feature_type=FeatureType(v.get("feature_type", "unknown")),
        )
    edges = []
    for ed in g_data.get("edges", []):
        edges.append(
            FeatureEdge(
                source=ed.get("source", ""),
                target=ed.get("target", ""),
                edge_type=ed.get("edge_type", ""),
                properties=dict(ed.get("properties", {})),
            )
        )
    graph = FeatureGraph(nodes=nodes, edges=edges)

    rel_profile = RelationshipProfile(
        graph=graph,
        pearson_matrix=dict(rel_data.get("pearson_matrix", {})),
        spearman_matrix=dict(rel_data.get("spearman_matrix", {})),
        mutual_information_scores=dict(rel_data.get("mutual_information_scores", {})),
        chi_square_p_values=dict(rel_data.get("chi_square_p_values", {})),
        cramers_v_matrix=dict(rel_data.get("cramers_v_matrix", {})),
        vif_scores=dict(rel_data.get("vif_scores", {})),
        target_correlation=dict(rel_data.get("target_correlation", {})),
        redundant_feature_groups=tuple(
            tuple(group) for group in rel_data.get("redundant_feature_groups", ())
        ),
    )

    rank_data = rs_data.get("ranking_profile", {})
    ranking_profile = RankingProfile(
        mutual_information=tuple(rank_data.get("mutual_information", ())),
        random_forest=tuple(rank_data.get("random_forest", ())),
        xgboost=tuple(rank_data.get("xgboost", ())),
        shap=tuple(rank_data.get("shap", ())),
        permutation_importance=tuple(rank_data.get("permutation_importance", ())),
        chi_square=tuple(rank_data.get("chi_square", ())),
        anova=tuple(rank_data.get("anova", ())),
        consensus_rrf=tuple(rank_data.get("consensus_rrf", ())),
    )

    reasoning_state = FeatureReasoningState(
        feature_profiles=profiles,
        relationship_profile=rel_profile,
        ranking_profile=ranking_profile,
        target_leakage_candidates=tuple(rs_data.get("target_leakage_candidates", ())),
        facts=dict(rs_data.get("facts", {})),
    )

    insights = []
    for ins in data.get("insights", []):
        insights.append(
            FeatureInsight(
                insight_id=ins.get("insight_id", ""),
                insight_type=ins.get("insight_type", ""),
                severity=ins.get("severity", ""),
                summary=ins.get("summary", ""),
                affected_columns=tuple(ins.get("affected_columns", ())),
                value=ins.get("value"),
                explanation=ins.get("explanation", ""),
            )
        )

    recommendations = []
    for rec in data.get("recommendations", []):
        c_data = rec.get("confidence", {})
        confidence = FeatureConfidence(
            score=c_data.get("score", 1.0),
            uncertainty=c_data.get("uncertainty", 0.0),
            supporting_evidence=tuple(c_data.get("supporting_evidence", ())),
            explanation=c_data.get("explanation", ""),
        )

        ev_data = rec.get("evidence", {})
        evidence = RecommendationEvidence(
            triggered_rules=tuple(ev_data.get("triggered_rules", ())),
            statistics_used=tuple(ev_data.get("statistics_used", ())),
            thresholds=dict(ev_data.get("thresholds", {})),
            supporting_features=tuple(ev_data.get("supporting_features", ())),
            notes=tuple(ev_data.get("notes", ())),
        )

        recommendations.append(
            FeatureRecommendation(
                recommendation_id=rec.get("recommendation_id", ""),
                action=RecommendationAction(rec.get("action", "KEEP")),
                target_columns=tuple(rec.get("target_columns", ())),
                reasoning=rec.get("reasoning", ""),
                confidence=confidence,
                evidence=evidence,
            )
        )

    proposals = []
    for prop in data.get("engineering_proposals", []):
        c_data = prop.get("confidence", {})
        confidence = FeatureConfidence(
            score=c_data.get("score", 1.0),
            uncertainty=c_data.get("uncertainty", 0.0),
            supporting_evidence=tuple(c_data.get("supporting_evidence", ())),
            explanation=c_data.get("explanation", ""),
        )

        lin_data = prop.get("lineage")
        lineage = None
        if lin_data:
            lineage = FeatureLineage(
                parent_features=tuple(lin_data.get("parent_features", ())),
                transformation=lin_data.get("transformation", ""),
                generation_step=lin_data.get("generation_step", 0),
            )

        proposals.append(
            FeatureEngineeringProposal(
                proposal_id=prop.get("proposal_id", ""),
                source_columns=tuple(prop.get("source_columns", ())),
                generated_feature=prop.get("generated_feature", ""),
                transformation=prop.get("transformation", ""),
                expected_gain=prop.get("expected_gain", 0.0),
                computational_cost=prop.get("computational_cost", "LOW"),
                confidence=confidence,
                lineage=lineage,
            )
        )

    session = FeatureSession(
        context=context,
        reasoning_state=reasoning_state,
        insights=insights,
        recommendations=recommendations,
        engineering_proposals=proposals,
        consensus_ranking=tuple(data.get("consensus_ranking", ())),
        status=data.get("status", "SUCCESS"),
    )

    if "id" in data:
        object.__setattr__(session, "id", UUID(data["id"]))
    if "created_at" in data:
        object.__setattr__(
            session, "created_at", datetime.fromisoformat(data["created_at"])
        )

    return session


def dict_to_reflection_session(data: dict) -> "ReflectionSession":
    """Helper to reconstruct a ReflectionSession from raw dict."""
    from mlos.domain.models.reflection.reflection_confidence import ReflectionConfidence
    from mlos.domain.models.reflection.reflection_feedback import ReflectionFeedback
    from mlos.domain.models.reflection.reflection_insight import ReflectionInsight
    from mlos.domain.models.reflection.reflection_session import ReflectionSession

    insights = []
    for item in data.get("insights", []):
        insights.append(
            ReflectionInsight(
                insight_id=item.get("insight_id", ""),
                insight_type=item.get("insight_type", ""),
                severity=item.get("severity", ""),
                summary=item.get("summary", ""),
                evidence=tuple(item.get("evidence", ())),
                confidence=item.get("confidence", 1.0),
            )
        )

    feedback = []
    for item in data.get("feedback", []):
        feedback.append(
            ReflectionFeedback(
                feedback_id=item.get("feedback_id", ""),
                target_subsystem=item.get("target_subsystem", ""),
                target_component=item.get("target_component", ""),
                action_type=item.get("action_type", ""),
                parameters=dict(item.get("parameters", {})),
                priority=item.get("priority", ""),
                reason=item.get("reason", ""),
                expected_outcome=item.get("expected_outcome", ""),
            )
        )

    conf_data = data.get("confidence")
    confidence = None
    if conf_data:
        confidence = ReflectionConfidence(
            score=conf_data.get("score", 0.0),
            uncertainty=conf_data.get("uncertainty", 0.0),
            evidence=tuple(conf_data.get("evidence", ())),
            explanation=conf_data.get("explanation", ""),
            accepted=conf_data.get("accepted", False),
        )

    session = ReflectionSession(
        summary=data.get("summary", ""),
        insights=insights,
        feedback=feedback,
        confidence=confidence,
    )
    if "id" in data:
        from uuid import UUID

        object.__setattr__(session, "id", UUID(data["id"]))
    if "created_at" in data:
        from datetime import datetime

        object.__setattr__(
            session, "created_at", datetime.fromisoformat(data["created_at"])
        )
    if "updated_at" in data:
        from datetime import datetime

        object.__setattr__(
            session, "updated_at", datetime.fromisoformat(data["updated_at"])
        )

    return session


def dict_to_learning_session(data: dict) -> "LearningSession":
    """Helper to reconstruct a LearningSession from raw dict."""
    from mlos.domain.models.learning.learning_confidence import LearningConfidence
    from mlos.domain.models.learning.learning_evidence import LearningEvidence
    from mlos.domain.models.learning.learning_session import LearningSession
    from mlos.domain.models.learning.learning_update import LearningUpdate
    from mlos.domain.models.learning.learning_update_type import LearningUpdateType

    updates = []
    for u in data.get("updates", []):
        ev_data = u.get("evidence", {})
        evidence = LearningEvidence(
            reflection_session_ids=tuple(ev_data.get("reflection_session_ids", ())),
            evaluation_session_ids=tuple(ev_data.get("evaluation_session_ids", ())),
            execution_session_ids=tuple(ev_data.get("execution_session_ids", ())),
            metrics_used=tuple(ev_data.get("metrics_used", ())),
            confidence_values=tuple(ev_data.get("confidence_values", ())),
            frequency_counts=dict(ev_data.get("frequency_counts", {})),
            trend_information=dict(ev_data.get("trend_information", {})),
            supporting_observations=tuple(ev_data.get("supporting_observations", ())),
        )
        u_type = LearningUpdateType(u.get("update_type"))
        updates.append(
            LearningUpdate(
                update_id=u.get("update_id", ""),
                update_type=u_type,
                target_subsystem=u.get("target_subsystem", ""),
                target_component=u.get("target_component", ""),
                parameters=dict(u.get("parameters", {})),
                evidence=evidence,
            )
        )

    conf_data = data.get("confidence")
    confidence = None
    if conf_data:
        confidence = LearningConfidence(
            score=conf_data.get("score", 0.0),
            uncertainty=conf_data.get("uncertainty", 0.0),
            evidence=tuple(conf_data.get("evidence", ())),
            explanation=conf_data.get("explanation", ""),
            accepted=conf_data.get("accepted", False),
        )

    session = LearningSession(
        summary=data.get("summary", ""), updates=updates, confidence=confidence
    )
    if "id" in data:
        from uuid import UUID

        object.__setattr__(session, "id", UUID(data["id"]))
    if "created_at" in data:
        from datetime import datetime

        object.__setattr__(
            session, "created_at", datetime.fromisoformat(data["created_at"])
        )
    if "updated_at" in data:
        from datetime import datetime

        object.__setattr__(
            session, "updated_at", datetime.fromisoformat(data["updated_at"])
        )

    return session


def dict_to_knowledge_session(data: dict) -> "KnowledgeSession":
    """Helper to reconstruct a KnowledgeSession from raw dict."""
    from mlos.domain.models.knowledge.knowledge_conflict import KnowledgeConflict
    from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession

    conflicts = []
    for c in data.get("conflicts", []):
        conflicts.append(
            KnowledgeConflict(
                conflict_id=c.get("conflict_id", ""),
                subsystem=c.get("subsystem", ""),
                component=c.get("component", ""),
                parameter_name=c.get("parameter_name", ""),
                competing_values=tuple(c.get("competing_values", ())),
                resolution_applied=c.get("resolution_applied", ""),
            )
        )

    promoted = [dict_to_knowledge_entry(e) for e in data.get("promoted_entries", [])]

    session = KnowledgeSession(
        summary=data.get("summary", ""), promoted_entries=promoted, conflicts=conflicts
    )
    if "id" in data:
        from uuid import UUID

        object.__setattr__(session, "id", UUID(data["id"]))
    if "created_at" in data:
        from datetime import datetime

        object.__setattr__(
            session, "created_at", datetime.fromisoformat(data["created_at"])
        )
    if "updated_at" in data:
        from datetime import datetime

        object.__setattr__(
            session, "updated_at", datetime.fromisoformat(data["updated_at"])
        )
    return session


def dict_to_knowledge_entry(data: dict) -> "KnowledgeEntry":
    """Helper to reconstruct a KnowledgeEntry from raw dict."""
    from datetime import datetime

    from mlos.domain.models.knowledge.knowledge_confidence import KnowledgeConfidence
    from mlos.domain.models.knowledge.knowledge_entry import KnowledgeEntry
    from mlos.domain.models.knowledge.knowledge_entry_type import KnowledgeEntryType
    from mlos.domain.models.knowledge.knowledge_status import KnowledgeStatus
    from mlos.domain.models.knowledge.knowledge_version import KnowledgeVersion

    v_data = data.get("version", {})
    version = KnowledgeVersion(
        version_number=v_data.get("version_number", 1),
        parent_entry_id=v_data.get("parent_entry_id"),
        timestamp=(
            datetime.fromisoformat(v_data["timestamp"])
            if "timestamp" in v_data
            else datetime.now()
        ),
        change_summary=v_data.get("change_summary", ""),
        reason=v_data.get("reason", ""),
        rollback_reference=v_data.get("rollback_reference"),
    )

    c_data = data.get("confidence", {})
    confidence = KnowledgeConfidence(
        score=c_data.get("score", 0.0),
        uncertainty=c_data.get("uncertainty", 0.0),
        support_count=c_data.get("support_count", 0),
        usage_history_count=c_data.get("usage_history_count", 0),
        explanation=c_data.get("explanation", ""),
    )

    k_type = KnowledgeEntryType(data["knowledge_type"])
    k_status = KnowledgeStatus(data["status"])

    entry = KnowledgeEntry(
        knowledge_id=data.get("knowledge_id", ""),
        knowledge_type=k_type,
        target_subsystem=data.get("target_subsystem", ""),
        target_component=data.get("target_component", ""),
        parameters=dict(data.get("parameters", {})),
        source_learning_sessions=tuple(data.get("source_learning_sessions", ())),
        evidence_summary=data.get("evidence_summary", ""),
        version=version,
        created_at=(
            datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now()
        ),
        last_used=(
            datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None
        ),
        usage_count=data.get("usage_count", 0),
        confidence=confidence,
        status=k_status,
        usage_metadata=dict(data.get("usage_metadata", {})),
    )
    return entry


def feature_session_to_dict(s: FeatureSession) -> dict:
    """Serialize FeatureSession to dict safely."""
    from datetime import datetime

    d = s.to_dict()
    if d.get("context"):
        ctx = d["context"]
        if (
            "observed_at" in ctx
            and isinstance(ctx["observed_at"], datetime)
            or "observed_at" in ctx
            and hasattr(ctx["observed_at"], "isoformat")
        ):
            ctx["observed_at"] = ctx["observed_at"].isoformat()
    if d.get("reasoning_state"):
        rs = d["reasoning_state"]
        if "feature_profiles" in rs:
            for col, prof in rs["feature_profiles"].items():
                if "feature_type" in prof and hasattr(prof["feature_type"], "value"):
                    prof["feature_type"] = prof["feature_type"].value
                if prof.get("quality_score"):
                    qs = prof["quality_score"]
                    if qs.get("confidence"):
                        c = qs["confidence"]
                        if "supporting_evidence" in c:
                            c["supporting_evidence"] = list(c["supporting_evidence"])
        if rs.get("relationship_profile"):
            rp = rs["relationship_profile"]
            if "redundant_feature_groups" in rp:
                rp["redundant_feature_groups"] = [
                    list(g) for g in rp["redundant_feature_groups"]
                ]
            if rp.get("graph"):
                g = rp["graph"]
                if "nodes" in g:
                    for k, node in g["nodes"].items():
                        if "feature_type" in node and hasattr(
                            node["feature_type"], "value"
                        ):
                            node["feature_type"] = node["feature_type"].value
                if "edges" in g:
                    g["edges"] = [dict(e) for e in g["edges"]]
        if rs.get("ranking_profile"):
            rk = rs["ranking_profile"]
            for k in [
                "mutual_information",
                "random_forest",
                "xgboost",
                "shap",
                "permutation_importance",
                "chi_square",
                "anova",
                "consensus_rrf",
            ]:
                if k in rk:
                    rk[k] = list(rk[k])
        if "target_leakage_candidates" in rs:
            rs["target_leakage_candidates"] = list(rs["target_leakage_candidates"])
    if "insights" in d:
        for ins in d["insights"]:
            if "affected_columns" in ins:
                ins["affected_columns"] = list(ins["affected_columns"])
    if "recommendations" in d:
        for rec in d["recommendations"]:
            if "action" in rec and hasattr(rec["action"], "value"):
                rec["action"] = rec["action"].value
            if "target_columns" in rec:
                rec["target_columns"] = list(rec["target_columns"])
            if (
                "confidence" in rec
                and rec["confidence"]
                and "supporting_evidence" in rec["confidence"]
            ):
                rec["confidence"]["supporting_evidence"] = list(
                    rec["confidence"]["supporting_evidence"]
                )
            if rec.get("evidence"):
                ev = rec["evidence"]
                for k in [
                    "triggered_rules",
                    "statistics_used",
                    "supporting_features",
                    "notes",
                ]:
                    if k in ev:
                        ev[k] = list(ev[k])
    if "engineering_proposals" in d:
        for prop in d["engineering_proposals"]:
            if "source_columns" in prop:
                prop["source_columns"] = list(prop["source_columns"])
            if (
                "confidence" in prop
                and prop["confidence"]
                and "supporting_evidence" in prop["confidence"]
            ):
                prop["confidence"]["supporting_evidence"] = list(
                    prop["confidence"]["supporting_evidence"]
                )
            if prop.get("lineage"):
                lin = prop["lineage"]
                if "parent_features" in lin:
                    lin["parent_features"] = list(lin["parent_features"])
    if "consensus_ranking" in d:
        d["consensus_ranking"] = list(d["consensus_ranking"])
    return d


def update_project_config_from_memory(
    project_root: Path, memory: ProjectMemory
) -> None:
    """
    Sync memory back into the lightweight configuration file.
    """
    config_file = project_root / ".mlos" / "project_config.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)

    from mlos.serialization import serialization_engine
    from mlos.serialization.version import SchemaVersion

    # Transparently serialize and save config
    yaml_str = serialization_engine.serialize(
        memory, SchemaVersion(3, 0, 0), format="yaml"
    )
    with open(config_file, "w") as f:
        f.write(yaml_str)


def meta_session_to_dict(s: MetaSession) -> dict:
    """Helper to convert MetaSession to dict."""

    def pc_to_dict(pc: ProviderCapability | None) -> dict | None:
        if pc is None:
            return None
        return {
            "provider_name": pc.provider_name,
            "model_name": pc.model_name,
            "structured_output_support": pc.structured_output_support,
            "reasoning_support": pc.reasoning_support,
            "tool_calling": pc.tool_calling,
            "streaming": pc.streaming,
            "context_window": pc.context_window,
            "latency_score": pc.latency_score,
            "estimated_cost_per_1k_input": pc.estimated_cost_per_1k_input,
            "estimated_cost_per_1k_output": pc.estimated_cost_per_1k_output,
            "offline_availability": pc.offline_availability,
        }

    def policy_to_dict(p: ExecutionPolicy) -> dict:
        pc = p.strategy.provider_selection
        return {
            "subsystem": p.subsystem.value,
            "strategy": {
                "algorithm_type": p.strategy.algorithm_type.value,
                "provider_selection": pc_to_dict(pc),
                "cache_policy": {
                    "max_age_seconds": p.strategy.cache_policy.max_age_seconds,
                    "force_refresh": p.strategy.cache_policy.force_refresh,
                    "cache_hit_action": p.strategy.cache_policy.cache_hit_action,
                },
                "validation_policy": {
                    "required_schemas": list(
                        p.strategy.validation_policy.required_schemas
                    ),
                    "fallback_on_failure": p.strategy.validation_policy.fallback_on_failure,
                    "validation_mode": p.strategy.validation_policy.validation_mode,
                },
                "retry_policy": {
                    "max_retries": p.strategy.retry_policy.max_retries,
                    "backoff_factor": p.strategy.retry_policy.backoff_factor,
                    "fallback_strategy": p.strategy.retry_policy.fallback_strategy,
                },
            },
            "resources": {
                "token_budget": p.resources.token_budget,
                "cost_budget_usd": p.resources.cost_budget_usd,
                "reasoning_budget": p.resources.reasoning_budget,
                "cpu_cores_limit": p.resources.cpu_cores_limit,
                "memory_limit_mb": p.resources.memory_limit_mb,
                "cache_usage_limit_mb": p.resources.cache_usage_limit_mb,
                "max_worker_limits": p.resources.max_worker_limits,
                "additional_resources": dict(p.resources.additional_resources),
            },
            "trace": {
                "triggered_rules": [
                    {
                        "rule_id": r.rule_id,
                        "condition_evaluated": r.condition_evaluated,
                        "action_taken": r.action_taken,
                    }
                    for r in p.trace.triggered_rules
                ],
                "evidence": {
                    "statistics_used": list(p.trace.evidence.statistics_used),
                    "observations_used": list(p.trace.evidence.observations_used),
                    "performance_metrics": dict(p.trace.evidence.performance_metrics),
                },
                "optimization_objectives": dict(p.trace.optimization_objectives),
                "confidence_score": p.trace.confidence_score,
            },
        }

    # Context
    c = s.context
    ctx_dict = {
        "project_name": c.project_name,
        "project_goal": c.project_goal,
        "observed_at": c.observed_at.isoformat(),
        "provider_registry": [pc_to_dict(p) for p in c.provider_registry],
        "user_constraints": {
            "token_budget": c.user_constraints.token_budget,
            "cost_budget_usd": c.user_constraints.cost_budget_usd,
            "cpu_cores_limit": c.user_constraints.cpu_cores_limit,
            "memory_limit_mb": c.user_constraints.memory_limit_mb,
        },
    }

    # State
    st = s.reasoning_state
    plan = st.execution_plan
    plan_dict = None
    if plan:
        plan_dict = {
            "planner_name": plan.planner_name,
            "planner_version": plan.planner_version,
            "generated_at": plan.generated_at.isoformat(),
            "checksum": plan.checksum,
            "optimization_result": dict(plan.optimization_result),
            "policy_version": {
                "policy_id": str(plan.policy_version.policy_id),
                "version": plan.policy_version.version,
                "generated_by": plan.policy_version.generated_by,
                "generated_at": plan.policy_version.generated_at.isoformat(),
            },
            "subsystem_policies": {
                k.value: policy_to_dict(v) for k, v in plan.subsystem_policies.items()
            },
            "execution_schedule": {
                "max_parallel_workers": plan.execution_schedule.max_parallel_workers,
                "nodes": [
                    {
                        "node_id": n.node_id,
                        "subsystem": n.subsystem.value,
                        "execution_condition": n.execution_condition,
                        "is_deferred": n.is_deferred,
                    }
                    for n in plan.execution_schedule.nodes
                ],
                "dependencies": [
                    {
                        "parent_node_id": d.parent_node_id,
                        "child_node_id": d.child_node_id,
                        "dependency_type": d.dependency_type,
                    }
                    for d in plan.execution_schedule.dependencies
                ],
            },
        }

    st_dict = {
        "optimization_objective_scores": dict(st.optimization_objective_scores),
        "facts": dict(st.facts),
        "execution_plan": plan_dict,
    }

    return {
        "context": ctx_dict,
        "reasoning_state": st_dict,
        "policy_version": {
            "policy_id": str(s.policy_version.policy_id),
            "version": s.policy_version.version,
            "generated_by": s.policy_version.generated_by,
            "generated_at": s.policy_version.generated_at.isoformat(),
        },
        "execution_lifecycle": s.execution_lifecycle.value,
    }


def dict_to_meta_session(data: dict) -> MetaSession:
    """Helper to reconstruct MetaSession from dict."""
    from datetime import datetime
    from uuid import UUID

    c_data = data.get("context", {})
    provider_registry = []
    for pr in c_data.get("provider_registry", []):
        if pr:
            provider_registry.append(
                ProviderCapability(
                    provider_name=pr.get("provider_name", ""),
                    model_name=pr.get("model_name", ""),
                    structured_output_support=pr.get("structured_output_support", True),
                    reasoning_support=pr.get("reasoning_support", True),
                    tool_calling=pr.get("tool_calling", True),
                    streaming=pr.get("streaming", True),
                    context_window=pr.get("context_window", 128000),
                    latency_score=pr.get("latency_score", 0.5),
                    estimated_cost_per_1k_input=pr.get(
                        "estimated_cost_per_1k_input", 0.0
                    ),
                    estimated_cost_per_1k_output=pr.get(
                        "estimated_cost_per_1k_output", 0.0
                    ),
                    offline_availability=pr.get("offline_availability", False),
                )
            )

    uc_data = c_data.get("user_constraints", {})
    user_constraints = ResourceAllocation(
        token_budget=uc_data.get("token_budget"),
        cost_budget_usd=uc_data.get("cost_budget_usd"),
        cpu_cores_limit=uc_data.get("cpu_cores_limit"),
        memory_limit_mb=uc_data.get("memory_limit_mb"),
    )

    from mlos.domain.models.knowledge_summary import KnowledgeSummary

    context = MetaContext(
        project_name=c_data.get("project_name", ""),
        project_goal=c_data.get("project_goal", ""),
        dataset_summary=None,
        feature_session=None,
        knowledge_summary=KnowledgeSummary(),
        provider_registry=tuple(provider_registry),
        user_constraints=user_constraints,
        feedback_evidence=HistoricalEvidence(),
        observed_at=datetime.fromisoformat(
            c_data.get("observed_at", datetime.utcnow().isoformat())
        ),
    )

    st_data = data.get("reasoning_state", {})
    plan_data = st_data.get("execution_plan")
    plan = None
    if plan_data:
        pv_data = plan_data.get("policy_version", {})
        policy_version = PolicyVersion(
            policy_id=UUID(pv_data.get("policy_id", str(uuid.uuid4()))),
            version=pv_data.get("version", 1),
            parent_policy_id=None,
            generated_by=pv_data.get("generated_by", ""),
            generated_at=datetime.fromisoformat(
                pv_data.get("generated_at", datetime.utcnow().isoformat())
            ),
            superseded_by=None,
            effective_from=datetime.fromisoformat(
                pv_data.get("generated_at", datetime.utcnow().isoformat())
            ),
        )

        subsystem_policies = {}
        for sub_val, pol_data in plan_data.get("subsystem_policies", {}).items():
            sub_name = SubsystemName(sub_val)
            strat_data = pol_data.get("strategy", {})
            pc_data = strat_data.get("provider_selection")
            pc = None
            if pc_data:
                pc = ProviderCapability(
                    provider_name=pc_data.get("provider_name", ""),
                    model_name=pc_data.get("model_name", ""),
                    structured_output_support=pc_data.get(
                        "structured_output_support", True
                    ),
                    reasoning_support=pc_data.get("reasoning_support", True),
                    tool_calling=pc_data.get("tool_calling", True),
                    streaming=pc_data.get("streaming", True),
                    context_window=pc_data.get("context_window", 128000),
                    latency_score=pc_data.get("latency_score", 0.5),
                    estimated_cost_per_1k_input=pc_data.get(
                        "estimated_cost_per_1k_input", 0.0
                    ),
                    estimated_cost_per_1k_output=pc_data.get(
                        "estimated_cost_per_1k_output", 0.0
                    ),
                    offline_availability=pc_data.get("offline_availability", False),
                )

            cp_data = strat_data.get("cache_policy", {})
            cache = CachePolicy(
                max_age_seconds=cp_data.get("max_age_seconds", 3600),
                force_refresh=cp_data.get("force_refresh", False),
                cache_hit_action=cp_data.get("cache_hit_action", "USE_CACHE"),
            )

            vp_data = strat_data.get("validation_policy", {})
            validation = ValidationPolicy(
                required_schemas=tuple(vp_data.get("required_schemas", ())),
                fallback_on_failure=vp_data.get("fallback_on_failure", True),
                validation_mode=vp_data.get("validation_mode", "LAX"),
            )

            rp_data = strat_data.get("retry_policy", {})
            retry = RetryPolicy(
                max_retries=rp_data.get("max_retries", 3),
                backoff_factor=rp_data.get("backoff_factor", 1.5),
                fallback_strategy=rp_data.get("fallback_strategy", "FALLBACK_TO_RULE"),
            )

            strategy = ExecutionStrategy(
                algorithm_type=ExecutionMode(strat_data.get("algorithm_type", "RULE")),
                provider_selection=pc,
                cache_policy=cache,
                validation_policy=validation,
                retry_policy=retry,
            )

            res_data = pol_data.get("resources", {})
            resources = ResourceAllocation(
                token_budget=res_data.get("token_budget"),
                cost_budget_usd=res_data.get("cost_budget_usd"),
                cpu_cores_limit=res_data.get("cpu_cores_limit"),
                memory_limit_mb=res_data.get("memory_limit_mb"),
            )

            trace_data = pol_data.get("trace", {})
            trace = DecisionTrace(
                triggered_rules=tuple(
                    [
                        DecisionRule(
                            rule_id=r.get("rule_id", ""),
                            condition_evaluated=r.get("condition_evaluated", ""),
                            action_taken=r.get("action_taken", ""),
                        )
                        for r in trace_data.get("triggered_rules", [])
                    ]
                ),
                evidence=DecisionEvidence(
                    statistics_used=tuple(
                        trace_data.get("evidence", {}).get("statistics_used", [])
                    ),
                    observations_used=tuple(
                        trace_data.get("evidence", {}).get("observations_used", [])
                    ),
                    performance_metrics=dict(
                        trace_data.get("evidence", {}).get("performance_metrics", {})
                    ),
                ),
                optimization_objectives=dict(
                    trace_data.get("optimization_objectives", {})
                ),
                confidence_score=trace_data.get("confidence_score", 1.0),
            )

            subsystem_policies[sub_name] = ExecutionPolicy(
                subsystem=sub_name,
                strategy=strategy,
                resources=resources,
                trace=trace,
            )

            sched_data = plan_data.get("execution_schedule", {})
            nodes = [
                ScheduleNode(
                    node_id=n.get("node_id", ""),
                    subsystem=SubsystemName(n.get("subsystem", "planning")),
                    execution_condition=n.get("execution_condition", "ALWAYS"),
                    is_deferred=n.get("is_deferred", False),
                )
                for n in sched_data.get("nodes", [])
            ]
            dependencies = [
                ScheduleDependency(
                    parent_node_id=d.get("parent_node_id", ""),
                    child_node_id=d.get("child_node_id", ""),
                    dependency_type=d.get("dependency_type", "SEQUENTIAL"),
                )
                for d in sched_data.get("dependencies", [])
            ]
            schedule = ExecutionSchedule(
                nodes=tuple(nodes),
                dependencies=tuple(dependencies),
                max_parallel_workers=sched_data.get("max_parallel_workers", 1),
            )

        plan = ExecutionPlan(
            policy_version=policy_version,
            subsystem_policies=subsystem_policies,
            execution_schedule=schedule,
            optimization_result=dict(plan_data.get("optimization_result", {})),
            planner_name=plan_data.get("planner_name", ""),
            planner_version=plan_data.get("planner_version", ""),
            generated_at=datetime.fromisoformat(
                plan_data.get("generated_at", datetime.utcnow().isoformat())
            ),
            checksum=plan_data.get("checksum", ""),
        )

    state = MetaReasoningState(
        execution_plan=plan,
        optimization_objective_scores=dict(
            st_data.get("optimization_objective_scores", {})
        ),
        facts=dict(st_data.get("facts", {})),
    )

    pv_sess_data = data.get("policy_version", {})
    policy_version_sess = PolicyVersion(
        policy_id=UUID(pv_sess_data.get("policy_id", str(uuid.uuid4()))),
        version=pv_sess_data.get("version", 1),
        parent_policy_id=None,
        generated_by=pv_sess_data.get("generated_by", ""),
        generated_at=datetime.fromisoformat(
            pv_sess_data.get("generated_at", datetime.utcnow().isoformat())
        ),
        superseded_by=None,
        effective_from=datetime.fromisoformat(
            pv_sess_data.get("generated_at", datetime.utcnow().isoformat())
        ),
    )

    return MetaSession(
        context=context,
        reasoning_state=state,
        policy_version=policy_version_sess,
        execution_lifecycle=ExecutionLifecycle(
            data.get("execution_lifecycle", "PLANNED")
        ),
    )


def execution_snapshot_to_dict(s: ExecutionSnapshot) -> dict:
    """Helper to convert ExecutionSnapshot to dict."""
    return {
        "run_id": str(s.run_id),
        "policy_version": {
            "policy_id": str(s.policy_version.policy_id),
            "version": s.policy_version.version,
            "generated_by": s.policy_version.generated_by,
            "generated_at": s.policy_version.generated_at.isoformat(),
        },
        "input_hash": s.input_hash,
        "output_hash": s.output_hash,
        "timestamps": {k: v.isoformat() for k, v in s.timestamps.items()},
        "execution_state_history": [
            [t.isoformat(), lifecycle.value]
            for t, lifecycle in s.execution_state_history
        ],
    }


def dict_to_execution_snapshot(data: dict) -> ExecutionSnapshot:
    """Helper to reconstruct ExecutionSnapshot from dict."""
    from datetime import datetime
    from uuid import UUID

    pv_data = data.get("policy_version", {})
    policy_version = PolicyVersion(
        policy_id=UUID(pv_data.get("policy_id", str(uuid.uuid4()))),
        version=pv_data.get("version", 1),
        parent_policy_id=None,
        generated_by=pv_data.get("generated_by", ""),
        generated_at=datetime.fromisoformat(
            pv_data.get("generated_at", datetime.utcnow().isoformat())
        ),
        superseded_by=None,
        effective_from=datetime.fromisoformat(
            pv_data.get("generated_at", datetime.utcnow().isoformat())
        ),
    )

    # Empty placeholder plan / schedule for snapshot reconstruction
    schedule = ExecutionSchedule(nodes=(), dependencies=(), max_parallel_workers=1)
    plan = ExecutionPlan(
        policy_version=policy_version,
        subsystem_policies={},
        execution_schedule=schedule,
        optimization_result={},
        planner_name="",
        planner_version="",
        generated_at=datetime.utcnow(),
        checksum="",
    )

    state_history = []
    for item in data.get("execution_state_history", []):
        state_history.append(
            (datetime.fromisoformat(item[0]), ExecutionLifecycle(item[1]))
        )

    return ExecutionSnapshot(
        run_id=UUID(data.get("run_id", str(uuid.uuid4()))),
        policy_version=policy_version,
        execution_plan=plan,
        execution_schedule=schedule,
        execution_state_history=tuple(state_history),
        telemetry=(),
        input_hash=data.get("input_hash", ""),
        output_hash=data.get("output_hash", ""),
        timestamps={
            k: datetime.fromisoformat(v) for k, v in data.get("timestamps", {}).items()
        },
    )
