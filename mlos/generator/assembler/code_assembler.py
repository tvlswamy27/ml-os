"""
Code Assembler.

Compiles GeneratedCode blocks into an in-memory PipelineSource.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.pipeline_source import PipelineSource


class CodeAssembler:
    """
    Assembles code snippets into a structured and clean script.
    """

    def assemble(self, generated_codes: list[GeneratedCode]) -> PipelineSource:
        """
        Deduplicates imports and merges code blocks sequentially.
        """
        all_imports = set()
        code_blocks = []

        for gc in generated_codes:
            for imp in gc.imports:
                all_imports.add(imp.strip())
            if gc.code:
                code_blocks.append(f"# Step: {gc.title}\n{gc.code.strip()}")

        imports_block = "\n".join(sorted(list(all_imports)))
        body_block = "\n\n".join(code_blocks)
        full_code = f"{imports_block}\n\n{body_block}\n".strip() + "\n"

        return PipelineSource(
            imports=imports_block,
            body=body_block,
            code=full_code,
        )
