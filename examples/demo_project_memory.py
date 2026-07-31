from mlos.domain.services.project_memory_service import ProjectMemoryService

memory_service = ProjectMemoryService()

memory = memory_service.create(
    project_name="Titanic",
    project_goal="Predict passenger survival",
)

print(memory)
