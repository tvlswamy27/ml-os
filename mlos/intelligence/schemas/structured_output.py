from typing import Any, Type, Union
from pydantic import BaseModel

# Represents the supported schemas: Pydantic classes, dict (JSON Schema), or basic dataclass/type types
StructuredOutputSchema = Union[Type[BaseModel], dict[str, Any], Type]
