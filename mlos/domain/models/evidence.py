from dataclasses import dataclass

@dataclass
class Evidence:

    metric: str

    value: str

    source: str