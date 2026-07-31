from dataclasses import dataclass


@dataclass(frozen=True)
class TokenUsage:
    """
    Represents input and output token consumption metrics.
    """

    input_tokens: int
    output_tokens: int
    total_tokens: int
