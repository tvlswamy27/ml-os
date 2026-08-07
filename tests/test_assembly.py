"""
Unit and integration tests for the ML-OS Artifact Assembly Subsystem.
"""

from pathlib import Path

from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.pipeline_source import PipelineSource
from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.services.assembly_service import AssemblyService
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.engine.engine import MLOSEngine
from mlos.generator.assembler.code_assembler import CodeAssembler
from mlos.generator.assembler.pipeline_assembly_engine import PipelineAssemblyEngine


def test_pipeline_source_instantiation():
    source = PipelineSource(
        imports="import pandas as pd",
        body="print('Hello')",
        code="import pandas as pd\n\nprint('Hello')",
    )
    assert source.imports == "import pandas as pd"
    assert source.body == "print('Hello')"
    assert source.code == "import pandas as pd\n\nprint('Hello')"


def test_code_assembler_merges_and_deduplicates():
    gc1 = GeneratedCode(
        title="Imputation",
        description="Missing values",
        imports=["import pandas as pd", "from sklearn.impute import SimpleImputer"],
        code="df['A'] = imputer.fit_transform(df[['A']])",
    )
    gc2 = GeneratedCode(
        title="Scaling",
        description="Standard scaler",
        imports=[
            "import pandas as pd",
            "from sklearn.preprocessing import StandardScaler",
        ],
        code="df['B'] = scaler.fit_transform(df[['B']])",
    )

    assembler = CodeAssembler()
    source = assembler.assemble([gc1, gc2])

    # Assert imports are deduplicated and sorted
    assert "import pandas as pd" in source.imports
    assert source.imports.count("import pandas as pd") == 1
    assert "from sklearn.impute import SimpleImputer" in source.imports
    assert "from sklearn.preprocessing import StandardScaler" in source.imports

    # Assert body block wraps steps
    assert "# Step: Imputation" in source.body
    assert "# Step: Scaling" in source.body
    assert "df['A'] = imputer.fit_transform" in source.body
    assert "df['B'] = scaler.fit_transform" in source.body


def test_pipeline_assembly_engine():
    assembler = CodeAssembler()
    engine = PipelineAssemblyEngine(assembler=assembler)

    gc = GeneratedCode(
        title="Dummy",
        description="Dummy test",
        imports=["import sys"],
        code="print('Dummy')",
    )

    source = engine.assemble([gc])
    assert source.imports == "import sys"
    assert "print('Dummy')" in source.code


def test_assembly_service_execution(tmp_path):
    # Set up memory
    memory = ProjectMemory(project_name="TestAssemblyProj", project_goal="TestGoal")

    # Override the root directory path in the test dynamically by patching Path in AssemblyService
    # Or simple hack: write_text to a customized path if we want, but wait, playground is relative.
    # We can temporarily patch the target path in tests or let it write to a specific location.
    # To keep it robust, let's mock or use the relative 'playground' path which pytest allows.
    # Wait, we can let it write to `playground/TestAssemblyProj` and then clean up the directory.

    gc = GeneratedCode(
        title="Step1",
        description="Goal description",
        imports=["import math"],
        code="print(math.sqrt(16))",
    )

    assembler = CodeAssembler()
    engine = PipelineAssemblyEngine(assembler=assembler)
    memory_service = ProjectMemoryService()
    assembly_service = AssemblyService(
        assembly_engine=engine, project_memory_service=memory_service
    )

    assembly_service.run_assembly(memory, [gc])

    # Assert Pipeline is registered to memory
    assert memory.pipeline is not None
    assert memory.pipeline.entrypoint_path.exists()
    assert memory.pipeline.entrypoint_path.name == "pipeline.py"

    # Assert code file matches
    content = memory.pipeline.entrypoint_path.read_text(encoding="utf-8")
    assert "import math" in content
    assert "print(math.sqrt(16))" in content

    # Clean up project dir
    project_dir = Path("playground") / "TestAssemblyProj"
    if project_dir.exists():
        import shutil

        shutil.rmtree(project_dir)


def test_full_generate_assemble_execute_integration(tmp_path):
    # Setup ML-OS Orchestrator
    engine = MLOSEngine()
    engine.create_project(name="IntegrationFlowProj", goal="Verify compile and run")

    # Create transient GeneratedCode
    gc1 = GeneratedCode(
        title="Setup",
        description="Print greeting",
        imports=["import sys"],
        code="print('Execution Start')",
    )
    gc2 = GeneratedCode(
        title="Math",
        description="Perform calculation",
        imports=["import math"],
        code="print(f'Result: {math.pow(2, 3)}')",
    )

    # 1. Assemble the generated codes
    engine.assemble([gc1, gc2])

    assert engine.project_memory.pipeline is not None
    assert engine.project_memory.pipeline.entrypoint_path.exists()

    # 2. Execute the compiled pipeline
    engine.execute()

    # 3. Verify execution results
    result = engine.project_memory.execution_result
    assert result is not None
    assert result.status == "SUCCESS"
    assert "Execution Start" in result.stdout
    assert "Result: 8.0" in result.stdout
    assert result.exit_code == 0

    # Clean up
    project_dir = Path("playground") / "IntegrationFlowProj"
    if project_dir.exists():
        import shutil

        shutil.rmtree(project_dir)
