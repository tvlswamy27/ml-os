"""
Pipeline Assembly Engine.

Entry point for compiling pipeline structures.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.pipeline_source import PipelineSource
from mlos.generator.assembler.code_assembler import CodeAssembler


class PipelineAssemblyEngine:
    """
    Stateless engine coordinating logical pipeline assembly.
    """

    def __init__(self, assembler: CodeAssembler):
        self.assembler = assembler

    def assemble(self, generated_codes: list[GeneratedCode]) -> PipelineSource:
        """
        Runs compilation logic to produce PipelineSource.
        """
        return self.assembler.assemble(generated_codes)
