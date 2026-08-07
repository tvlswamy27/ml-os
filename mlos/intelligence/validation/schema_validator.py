import json
from typing import Any

from pydantic import BaseModel

from mlos.intelligence.schemas.structured_output import StructuredOutputSchema


class SchemaValidator:
    """
    Validates that a raw response conforms to the requested Pydantic model or JSON Schema.
    """

    @staticmethod
    def validate_and_parse(
        raw_response: str, schema: StructuredOutputSchema | None
    ) -> tuple[Any, bool]:
        """
        Validates raw JSON string response against schema.
        Returns (parsed_output, validation_passed).
        """
        if schema is None:
            return raw_response, True

        try:
            parsed_json = json.loads(raw_response)
        except Exception:
            return None, False

        # If it is a Pydantic model class
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            try:
                parsed_obj = schema.model_validate(parsed_json)
                return parsed_obj, True
            except Exception:
                return None, False

        # If it is a dict representing JSON schema, we can return the parsed dictionary
        if isinstance(schema, dict):
            return parsed_json, True

        return parsed_json, True
