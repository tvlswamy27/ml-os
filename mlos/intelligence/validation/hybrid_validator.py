from typing import Any, Callable


class HybridValidator:
    """
    Validates LLM-generated output against custom business rules and safety boundaries,
    supporting automated fallback.
    """

    @staticmethod
    def validate_constraints(
        parsed_output: Any,
        constraint_checker: Callable[[Any], bool] | None = None,
        fallback_value: Any = None,
    ) -> tuple[Any, bool]:
        """
        Runs programmatic validation checks on the parsed output.
        If validation fails, returns (fallback_value, False), otherwise (parsed_output, True).
        """
        if constraint_checker is None:
            return parsed_output, True

        try:
            is_valid = constraint_checker(parsed_output)
            if is_valid:
                return parsed_output, True
            else:
                return fallback_value, False
        except Exception:
            return fallback_value, False
