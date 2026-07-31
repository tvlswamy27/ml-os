"""
Generation Service.

Translates ProjectMemory to GenerationContext and orchestrates code generation.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.generation_context import GenerationContext
from mlos.generator.generator_engine import GeneratorEngine
from mlos.domain.services.project_memory_service import ProjectMemoryService


class GenerationService:
    """
    Coordinates building generation contexts, executing generator engines, and persisting intermediate generated codes.
    """

    def __init__(
        self,
        generation_engine: GeneratorEngine,
        project_memory_service: ProjectMemoryService,
    ):
        self.generation_engine = generation_engine
        self.project_memory_service = project_memory_service

    def build_context(self, memory: ProjectMemory) -> GenerationContext:
        """
        Translate ProjectMemory into an immutable GenerationContext.
        """
        decisions = tuple(memory.decisions)
        return GenerationContext(project_memory=memory, decisions=decisions)

    def run_generation(self, context: GenerationContext) -> list[GeneratedCode]:
        """
        Accept only a GenerationContext, invoke the GeneratorEngine, and return generated codes.
        """
        return self.generation_engine.generate(context)

    def generate(self, memory: ProjectMemory) -> list[GeneratedCode]:
        """
        Orchestrate the complete generation flow.
        """
        context = self.build_context(memory)
        generated_codes = self.run_generation(context)
        self.project_memory_service.update_generated_codes(memory, generated_codes)
        return generated_codes
