from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActiveRuleSummary:
    """
    Lightweight, immutable summary of an active knowledge rule.
    """

    subsystem: str
    component: str
    parameters: dict[str, str] = field(default_factory=dict)
    confidence_score: float = 1.0
    version_number: int = 1


@dataclass(frozen=True)
class KnowledgeSummary:
    """
    Collection of active rule summaries available to Planning and Decision.
    """

    rules: tuple[ActiveRuleSummary, ...] = field(default_factory=tuple)


def build_knowledge_summary(memory) -> KnowledgeSummary:
    """
    Translates active knowledge entries from ProjectMemory into a KnowledgeSummary.
    """
    from mlos.domain.models.knowledge.knowledge_status import KnowledgeStatus

    rules = []
    # Safeguard for backward compatibility
    entries = getattr(memory, "knowledge_entries", []) or []
    for entry in entries:
        if entry.status == KnowledgeStatus.ACTIVE:
            rules.append(
                ActiveRuleSummary(
                    subsystem=entry.target_subsystem,
                    component=entry.target_component,
                    parameters=dict(entry.parameters),
                    confidence_score=(
                        entry.confidence.score if entry.confidence else 1.0
                    ),
                    version_number=entry.version.version_number if entry.version else 1,
                )
            )
    return KnowledgeSummary(rules=tuple(rules))
