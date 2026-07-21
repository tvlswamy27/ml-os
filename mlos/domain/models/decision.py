from dataclasses import dataclass

@dataclass
class Decision:

    title: str

    reason: str

    confidence: float