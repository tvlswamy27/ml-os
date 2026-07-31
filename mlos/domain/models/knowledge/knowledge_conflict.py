from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeConflict:
    """
    Records conflicts identified between concurrent updates or historical settings and active selections.
    """

    conflict_id: str
    subsystem: str
    component: str
    parameter_name: str
    competing_values: tuple[str, ...]
    resolution_applied: str
