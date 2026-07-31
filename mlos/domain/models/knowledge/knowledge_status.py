from enum import Enum


class KnowledgeStatus(str, Enum):
    """
    Life cycle states of a persistent knowledge entry.
    """

    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    DISABLED = "DISABLED"
    EXPERIMENTAL = "EXPERIMENTAL"
