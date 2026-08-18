"""
Assembly Service.

Coordinates in-memory compilation and workspace file writing.

Author: Vikram Tanakala
License: MIT
"""

from pathlib import Path

from mlos.cli.persistence import find_project_root
from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.pipeline import Pipeline
from mlos.domain.models.pipeline_source import PipelineSource
from mlos.domain.models.project_memory import ProjectMemory
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

    def assemble(
        self, memory: ProjectMemory, project_root: Path | str | None = None
    ) -> PipelineSource:
        """
        Assemble code list stored in ProjectMemory.generated_codes, save python pipeline,
        and update ProjectMemory.
        """
        generated_codes = memory.generated_codes
        if not generated_codes:
            # Empty decisions/generated_codes -> return empty PipelineSource with no exceptions
            source = PipelineSource(imports="", body="", code="")
            self.project_memory_service.update_pipeline_source(memory, source)
            return source

        # Compile in-memory pipeline source code
        source = self.assembly_engine.assemble(generated_codes)

        # Resolve paths
        project_dir = (
            Path(project_root) if project_root else (find_project_root() or Path.cwd())
        )
        artifacts_dir = project_dir / "artifacts"

        artifacts_dir.mkdir(parents=True, exist_ok=True)
        entrypoint_path = artifacts_dir / "pipeline.py"

        # Resolve dataset path for pipeline script execution
        dataset_path_str = ""
        if memory.dataset and memory.dataset.path:
            dataset_path_str = str(Path(memory.dataset.path).as_posix())

        loader_code = ""
        if dataset_path_str:
            suffix = Path(dataset_path_str).suffix.lower()
            read_func = "read_parquet" if suffix == ".parquet" else "read_csv"
            loader_code = f"""import pandas as pd
df = pd.{read_func}("{dataset_path_str}")
"""

        # Write execution pipeline
        entrypoint_path.write_text(loader_code + "\n" + source.code, encoding="utf-8")

        # Instantiate Pipeline domain model and record to ProjectMemory
        pipeline = Pipeline(entrypoint_path=entrypoint_path.resolve())
        self.project_memory_service.update_pipeline(memory, pipeline)
        self.project_memory_service.update_pipeline_source(memory, source)

        return source

    def run_assembly(
        self,
        memory: ProjectMemory,
        generated_codes: list[GeneratedCode],
    ) -> None:
        """
        Backward compatible run_assembly delegation.
        """
        self.project_memory_service.update_generated_codes(memory, generated_codes)
        self.assemble(memory)
