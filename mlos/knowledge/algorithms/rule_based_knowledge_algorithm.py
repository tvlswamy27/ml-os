from datetime import datetime
from uuid import uuid4
from mlos.domain.models.knowledge.knowledge_status import KnowledgeStatus
from mlos.domain.models.knowledge.knowledge_entry_type import KnowledgeEntryType
from mlos.domain.models.knowledge.knowledge_confidence import KnowledgeConfidence
from mlos.domain.models.knowledge.knowledge_version import KnowledgeVersion
from mlos.domain.models.knowledge.knowledge_conflict import KnowledgeConflict
from mlos.domain.models.knowledge.knowledge_entry import KnowledgeEntry
from mlos.domain.models.knowledge.knowledge_context import (
    KnowledgeContext,
    LearningSummary,
    LearningUpdateSummary,
)
from mlos.domain.models.knowledge.knowledge_reasoning_state import (
    ProposedKnowledgeUpdate,
    KnowledgeReasoningState,
)
from mlos.domain.models.knowledge.knowledge_session import KnowledgeSession
from mlos.knowledge.algorithms.knowledge_algorithm import KnowledgeAlgorithm


class RuleBasedKnowledgeAlgorithm(KnowledgeAlgorithm):
    """
    Concrete KnowledgeAlgorithm that processes learning updates, detects and resolves
    parameter conflicts, and versions promoted active/experimental entries.
    """

    def can_manage(self, context: KnowledgeContext) -> bool:
        """Always capable of execution."""
        return True

    def _analyze_updates(self, context: KnowledgeContext) -> KnowledgeReasoningState:
        """Parses incoming learning updates into strongly typed ProposedKnowledgeUpdate objects."""
        incoming = []

        # Include latest learning updates
        if context.latest_learning is not None:
            l_session = context.latest_learning
            for u in l_session.updates:
                # Map string update type to KnowledgeEntryType Enum
                raw_type = u.update_type.upper()
                mapped_type = KnowledgeEntryType.PIPELINE_PREFERENCE

                if "WEIGHT" in raw_type:
                    mapped_type = KnowledgeEntryType.HEURISTIC_WEIGHT
                elif "PRIOR" in raw_type:
                    mapped_type = KnowledgeEntryType.PARAMETER_PRIOR
                elif "BLACKLIST" in raw_type:
                    mapped_type = KnowledgeEntryType.GENERATOR_BLACKLIST
                elif "WHITELIST" in raw_type:
                    mapped_type = KnowledgeEntryType.GENERATOR_WHITELIST
                elif "MODEL" in raw_type:
                    mapped_type = KnowledgeEntryType.MODEL_PREFERENCE
                elif "THRESHOLD" in raw_type:
                    mapped_type = KnowledgeEntryType.EVALUATION_THRESHOLD

                incoming.append(
                    ProposedKnowledgeUpdate(
                        update_id=u.update_id,
                        entry_type=mapped_type,
                        target_subsystem=u.target_subsystem,
                        target_component=u.target_component,
                        parameters=dict(u.parameters),
                        learning_session_id=l_session.session_id,
                        confidence_score=u.confidence_score,
                        evidence_summary=(
                            ", ".join(u.evidence_observations)
                            if u.evidence_observations
                            else "No evidence observations."
                        ),
                    )
                )

        # Determine starting max version from existing knowledge entries
        max_ver = 0
        if context.existing_knowledge is not None:
            for entry in context.existing_knowledge.active_entries:
                max_ver = max(max_ver, entry.version.version_number)

        return KnowledgeReasoningState(
            incoming_updates=tuple(incoming), current_max_version=max_ver
        )

    def _detect_conflicts(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        """Scans incoming updates and existing entries to identify competing parameter settings."""
        # For detect conflicts, we group incoming updates by target component and parameter keys.
        # This phase only detects; resolution is performed in the resolve phase.
        conflicts = []
        updates_by_target: dict[str, list[ProposedKnowledgeUpdate]] = {}
        for u in state.incoming_updates:
            key = f"{u.target_subsystem}:{u.target_component}"
            updates_by_target.setdefault(key, []).append(u)

        for key, list_upd in updates_by_target.items():
            if len(list_upd) > 1:
                # Compile parameter keys being modified
                all_params: set[str] = set()
                for u in list_upd:
                    all_params.update(u.parameters.keys())

                subsystem, component = key.split(":")
                for param in all_params:
                    # Collect competing values
                    competing = []
                    for u in list_upd:
                        if param in u.parameters:
                            competing.append(
                                f"{u.parameters[param]} (conf={u.confidence_score:.2f})"
                            )

                    if len(set(competing)) > 1:
                        conflicts.append(
                            KnowledgeConflict(
                                conflict_id=str(uuid4()),
                                subsystem=subsystem,
                                component=component,
                                parameter_name=param,
                                competing_values=tuple(competing),
                                resolution_applied="Pending Resolution",
                            )
                        )

        return KnowledgeReasoningState(
            incoming_updates=state.incoming_updates,
            detected_conflicts=tuple(conflicts),
            current_max_version=state.current_max_version,
        )

    def _resolve_conflicts(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        """Resolves overlapping parameter configurations using V1 deterministic priority rules."""
        resolved_updates: list[ProposedKnowledgeUpdate] = []
        conflicts = list(state.detected_conflicts)

        # Group all incoming updates by unique component target & entry type
        grouped: dict[tuple[str, KnowledgeEntryType], list[ProposedKnowledgeUpdate]] = (
            {}
        )
        for u in state.incoming_updates:
            grouped.setdefault((u.target_component, u.entry_type), []).append(u)

        for (comp, etype), candidates in grouped.items():
            if len(candidates) == 1:
                resolved_updates.append(candidates[0])
            else:
                # Deterministic conflict resolution V1:
                # 1. Higher learning confidence wins.
                # 2. If equal, newest wins (represented by order/last in list).
                winner = candidates[0]
                for cand in candidates[1:]:
                    if cand.confidence_score > winner.confidence_score:
                        winner = cand
                    elif cand.confidence_score == winner.confidence_score:
                        # Newest wins
                        winner = cand

                resolved_updates.append(winner)

                # Record conflict logs for losing updates
                for cand in candidates:
                    if cand.update_id != winner.update_id:
                        for param, val in cand.parameters.items():
                            conf_log = KnowledgeConflict(
                                conflict_id=str(uuid4()),
                                subsystem=cand.target_subsystem,
                                component=cand.target_component,
                                parameter_name=param,
                                competing_values=(
                                    f"{val} (Rejected)",
                                    f"{winner.parameters.get(param, '')} (Accepted)",
                                ),
                                resolution_applied="Higher learning confidence priority wins.",
                            )
                            conflicts.append(conf_log)

        # Update resolutions status in logged conflicts
        updated_conflicts = []
        for c in conflicts:
            if c.resolution_applied == "Pending Resolution":
                updated_conflicts.append(
                    KnowledgeConflict(
                        conflict_id=c.conflict_id,
                        subsystem=c.subsystem,
                        component=c.component,
                        parameter_name=c.parameter_name,
                        competing_values=c.competing_values,
                        resolution_applied="Highest learning confidence score priority applied.",
                    )
                )
            else:
                updated_conflicts.append(c)

        # Temporary save resolved proposed updates to state candidate items
        return KnowledgeReasoningState(
            incoming_updates=tuple(resolved_updates),
            detected_conflicts=tuple(updated_conflicts),
            current_max_version=state.current_max_version,
        )

    def _determine_promotions(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        """Decides promotions and maps the status: ACTIVE if score >= 0.70, EXPERIMENTAL if score < 0.70."""
        promoted_entries = []

        # In V1, we promote all resolved incoming updates.
        # If confidence is high (>= 0.7), it gets promoted as ACTIVE.
        # Otherwise, it gets promoted as EXPERIMENTAL.
        for u in state.incoming_updates:
            # We construct a temporary unresolved entry placeholder.
            # Versioning and unique parent references are mapped in the next phase.
            p_status = (
                KnowledgeStatus.ACTIVE
                if u.confidence_score >= 0.70
                else KnowledgeStatus.EXPERIMENTAL
            )

            # Map a temp KnowledgeEntry placeholder
            entry = KnowledgeEntry(
                knowledge_id=u.update_id,  # temporary id mapped from update_id
                knowledge_type=u.entry_type,
                target_subsystem=u.target_subsystem,
                target_component=u.target_component,
                parameters=dict(u.parameters),
                source_learning_sessions=(u.learning_session_id,),
                evidence_summary=u.evidence_summary,
                version=KnowledgeVersion(
                    version_number=1,
                    parent_entry_id=None,
                    timestamp=datetime.now(),
                    change_summary="",
                    reason="",
                ),
                created_at=datetime.now(),
                last_used=None,
                usage_count=0,
                confidence=KnowledgeConfidence(
                    score=u.confidence_score,
                    uncertainty=0.0,
                    support_count=1,
                    usage_history_count=0,
                    explanation="",
                ),
                status=p_status,
            )
            promoted_entries.append(entry)

        return KnowledgeReasoningState(
            incoming_updates=state.incoming_updates,
            detected_conflicts=state.detected_conflicts,
            resolved_entries=tuple(promoted_entries),
            current_max_version=state.current_max_version,
        )

    def _version_knowledge(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> KnowledgeReasoningState:
        """Increments version counters and assigns unique parent entry ID links."""
        final_entries = []

        # Existing active entries list
        existing_entries = []
        if context.existing_knowledge is not None:
            existing_entries = list(context.existing_knowledge.active_entries)

        for temp_entry in state.resolved_entries:
            # Check if there is an existing entry for same component and entry type
            parent_entry = None
            for old in existing_entries:
                if (
                    old.target_component == temp_entry.target_component
                    and old.knowledge_type == temp_entry.knowledge_type
                    and old.status
                    in (KnowledgeStatus.ACTIVE, KnowledgeStatus.EXPERIMENTAL)
                ):
                    parent_entry = old
                    break

            if parent_entry is not None:
                new_ver_num = parent_entry.version.version_number + 1
                parent_id = parent_entry.knowledge_id
            else:
                new_ver_num = 1
                parent_id = None

            version_meta = KnowledgeVersion(
                version_number=new_ver_num,
                parent_entry_id=parent_id,
                timestamp=datetime.now(),
                change_summary=f"Promoted update to version {new_ver_num}.",
                reason=temp_entry.evidence_summary,
            )

            # Reconstruct final entry with globally unique UUID
            promoted_entry = KnowledgeEntry(
                knowledge_id=str(uuid4()),
                knowledge_type=temp_entry.knowledge_type,
                target_subsystem=temp_entry.target_subsystem,
                target_component=temp_entry.target_component,
                parameters=dict(temp_entry.parameters),
                source_learning_sessions=temp_entry.source_learning_sessions,
                evidence_summary=temp_entry.evidence_summary,
                version=version_meta,
                created_at=datetime.now(),
                last_used=None,
                usage_count=0,
                confidence=temp_entry.confidence,
                status=temp_entry.status,
            )
            final_entries.append(promoted_entry)

        return KnowledgeReasoningState(
            incoming_updates=state.incoming_updates,
            detected_conflicts=state.detected_conflicts,
            resolved_entries=tuple(final_entries),
            current_max_version=state.current_max_version,
        )

    def _build_confidence(
        self, context: KnowledgeContext, state: KnowledgeReasoningState
    ) -> dict:
        """Calculates final confidence for each promoted knowledge entry."""
        confidence_details = {}

        # Calculate support counts using historical learnings
        for entry in state.resolved_entries:
            support_sessions = 1
            for hist in context.historical_learnings:
                # Check if this target component was also recommended in historical learnings
                for hist_upd in hist.updates:
                    if hist_upd.target_component == entry.target_component:
                        support_sessions += 1

            # Build final explainable KnowledgeConfidence
            score = entry.confidence.score
            uncertainty = max(0.0, 1.0 - (score * (0.8 + 0.1 * support_sessions)))

            conf_details = KnowledgeConfidence(
                score=score,
                uncertainty=uncertainty,
                support_count=support_sessions,
                usage_history_count=0,
                explanation=f"Confidence compiled with support of {support_sessions} learning sessions.",
            )
            confidence_details[entry.knowledge_id] = conf_details

        return confidence_details

    def _construct_session(
        self, state: KnowledgeReasoningState, confidence_details: dict
    ) -> KnowledgeSession:
        """Assembles variables into the final, frozen KnowledgeSession object."""
        # Re-attach updated confidence metrics to resolved entries
        promoted = []
        for entry in state.resolved_entries:
            if entry.knowledge_id in confidence_details:
                object.__setattr__(
                    entry, "confidence", confidence_details[entry.knowledge_id]
                )
            promoted.append(entry)

        summary = (
            f"Knowledge lifecycle promoted {len(promoted)} new policies, "
            f"identifying {len(state.detected_conflicts)} conflicts resolved."
        )

        return KnowledgeSession(
            summary=summary,
            promoted_entries=promoted,
            conflicts=list(state.detected_conflicts),
        )
