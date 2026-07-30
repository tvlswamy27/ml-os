"""
Assembly Service.

Coordinates in-memory compilation and workspace file writing.

Author: Vikram Tanakala
License: MIT
"""

from pathlib import Path

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.pipeline import Pipeline
from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.generator.assembler.pipeline_assembly_engine import PipelineAssemblyEngine


class AssemblyService:
    """
    Coordinates building and saving pipeline artifacts.
    """

    def __init__(
        self,
        assembly_engine: PipelineAssemblyEngine,
        project_memory_service: ProjectMemoryService,
    ):
        self.assembly_engine = assembly_engine
        self.project_memory_service = project_memory_service

    def run_assembly(
        self,
        memory: ProjectMemory,
        generated_codes: list[GeneratedCode],
    ) -> None:
        """
        Assemble code list, save python pipeline, and update ProjectMemory.
        """
        if not generated_codes:
            raise RuntimeError("No generated code exists to assemble.")

        # Compile in-memory pipeline source code
        source = self.assembly_engine.assemble(generated_codes)

        # Resolve paths
        project_dir = Path("playground") / memory.project_name
        artifacts_dir = project_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        entrypoint_path = artifacts_dir / "pipeline.py"

        # Write execution pipeline
        entrypoint_path.write_text(source.code, encoding="utf-8")

        # Future pipeline configuration files can be generated here

        # Instantiate Pipeline domain model and record to ProjectMemory
        pipeline = Pipeline(entrypoint_path=entrypoint_path.resolve())
        self.project_memory_service.update_pipeline(memory, pipeline)
