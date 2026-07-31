from mlos.reasoning.reasoning_engine import ReasoningEngine
from mlos.domain.services.project_memory_service import ProjectMemoryService

memory = ProjectMemoryService().create(
    "Titanic",
    "Predict passenger survival",
)

engine = ReasoningEngine()

recommendations = engine.reason(memory)

print(recommendations)
