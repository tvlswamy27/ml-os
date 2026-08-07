from typing import Any, Union

from pydantic import BaseModel

# Represents the supported schemas: Pydantic classes, dict (JSON Schema), or basic dataclass/type types
StructuredOutputSchema = Union[type[BaseModel], dict[str, Any], type]
