"""
Unit and integration tests for Planning, Decision, and Generation subsystem integration.
"""

from unittest.mock import MagicMock
import pytest

from mlos.domain.models.project_memory import ProjectMemory
from mlos.domain.models.generation_context import GenerationContext
from mlos.domain.models.generated_code import GeneratedCode
from mlos.domain.models.decision import Decision
from mlos.domain.models.pipeline_source import PipelineSource
from mlos.generator.generator_engine import GeneratorEngine
from mlos.domain.services.generation_service import GenerationService
from mlos.domain.services.project_memory_service import ProjectMemoryService
from mlos.generator.generators.missing_value_generator import MissingValueGenerator
from mlos.generator.generators.encoding_generator import EncodingGenerator
from mlos.generator.generators.scaling_generator import ScalingGenerator
from mlos.generator.generators.split_generator import SplitGenerator
from mlos.generator.generators.model_generator import ModelGenerator
from mlos.generator.assembler.code_assembler import CodeAssembler
from mlos.generator.assembler.pipeline_assembly_engine import PipelineAssemblyEngine
from mlos.domain.services.assembly_service import AssemblyService
from mlos.workflow.workflow_engine import WorkflowEngine
from mlos.workflow.workflow_hooks import HookRegistry
from mlos.engine.engine import MLOSEngine


def test_generation_context_construction():
    """
    Verify GenerationContext resolves decisions from ProjectMemory.
    """
    memory = ProjectMemory(project_name="TestProj", project_goal="TestGoal")
    decisions = [
        Decision(
            title="Missing Value Strategy: col1",
            strategy="Median Imputation",
            confidence="High",
            reason="Test",
        ),
        Decision(
            title="Encoding Strategy: col2",
            strategy="One-Hot Encoding",
            confidence="High",
            reason="Test",
        ),
    ]
    memory.decisions = decisions

    service = GenerationService(MagicMock(spec=GeneratorEngine), ProjectMemoryService())
    ctx = service.build_context(memory)
    assert ctx.project_memory == memory
    assert len(ctx.decisions) == 2
    assert ctx.decisions[0] == decisions[0]
    assert ctx.decisions[1] == decisions[1]


def test_generator_registry_dispatch_and_unknown():
    """
    Verify GenerationEngine dispatches to the correct registry generators and ignores unknown decisions gracefully.
    """
    generators = [
        MissingValueGenerator(),
        EncodingGenerator(),
    ]
    engine = GeneratorEngine(generators)

    decisions = (
        Decision(
            title="Missing Value Strategy: col1",
            strategy="Median Imputation",
            confidence="High",
            reason="Test",
        ),
        Decision(
            title="Encoding Strategy: col2",
            strategy="One-Hot Encoding",
            confidence="High",
            reason="Test",
        ),
        Decision(
            title="Unknown Decision: col3",
            strategy="Random Strategy",
            confidence="Low",
            reason="Test",
        ),
    )
    memory = ProjectMemory(project_name="TestProj", project_goal="TestGoal")
    context = GenerationContext(project_memory=memory, decisions=decisions)

    generated = engine.generate(context)

    # 3 decisions, but 1 is unknown, so only 2 generated codes should result
    assert len(generated) == 2
    assert "Missing Value Strategy" in generated[0].title
    assert "Encoding Strategy" in generated[1].title
    assert "SimpleImputer" in generated[0].imports[0]
    assert "pandas" in generated[1].imports[0]


def test_empty_generation_and_assembly():
    """
    Verify that empty decisions produce empty generated codes and empty pipeline source with no exceptions.
    """
    memory = ProjectMemory(project_name="EmptyProj", project_goal="Test")

    # 1. Empty decisions on GenerationService
    engine = GeneratorEngine([MissingValueGenerator(), EncodingGenerator()])
    gen_service = GenerationService(engine, ProjectMemoryService())
    codes = gen_service.generate(memory)

    assert len(codes) == 0
    assert len(memory.generated_codes) == 0

    # 2. Empty generated codes on AssemblyService
    assembly_engine = PipelineAssemblyEngine(CodeAssembler())
    assembly_service = AssemblyService(assembly_engine, ProjectMemoryService())
    source = assembly_service.assemble(memory)

    assert isinstance(source, PipelineSource)
    assert source.imports == ""
    assert source.body == ""
    assert source.code == ""
    assert memory.pipeline_source == source


def test_generation_service_orchestration():
    """
    Verify GenerationService.generate() orchestrates context building, generation execution,
    and memory persistence correctly.
    """
    memory = ProjectMemory(project_name="TestProj", project_goal="TestGoal")
    decisions = [
        Decision(
            title="Missing Value Strategy: col1",
            strategy="Median Imputation",
            confidence="High",
            reason="Test",
        )
    ]
    memory.decisions = decisions

    mock_engine = MagicMock(spec=GeneratorEngine)
    codes = [
        GeneratedCode(
            title="Missing Value Strategy: col1",
            description="Test",
            imports=["imp"],
            code="c = 1",
        )
    ]
    mock_engine.generate.return_value = codes

    service = GenerationService(mock_engine, ProjectMemoryService())
    res = service.generate(memory)

    assert res == codes
    assert len(memory.generated_codes) == 1
    assert memory.generated_codes[0] == codes[0]


def test_workflow_engine_generation_assembly_sequence():
    """
    Verify that WorkflowEngine runs Generation then Assembly in the correct chronological order.
    """

    class OrderTrackingMLOSEngine:
        def __init__(self):
            self.project_memory = ProjectMemory(
                project_name="WorkflowProj", project_goal="Test"
            )
            self.execution_engine = MagicMock()
            self.decision_engine = MagicMock()
            self.decision_service = MagicMock()
            self.intelligence_engine = MagicMock()

            self.execution_engine.execute.return_value = MagicMock()
            self.decision_service.decide.return_value = []

            self.call_order = []

        def analyze(self, path):
            self.call_order.append("analyze")

        def assemble(self):
            self.call_order.append("assemble")

        def execute(self):
            self.call_order.append("execute")

        def evaluate(self):
            self.call_order.append("evaluate")

    engine = OrderTrackingMLOSEngine()

    mock_planning_service = MagicMock()
    mock_planning_service.plan.return_value = MagicMock()

    mock_generation_service = MagicMock(spec=GenerationService)

    def gen_mock(mem):
        engine.call_order.append("generate")
        return []

    mock_generation_service.generate.side_effect = gen_mock

    hooks = HookRegistry()
    workflow = WorkflowEngine(
        mlos_engine=engine,
        hooks=hooks,
        planning_service=mock_planning_service,
        decision_service=engine.decision_service,
        generation_service=mock_generation_service,
    )

    res = workflow.run("dummy.csv")
    assert res.status == "SUCCESS"

    # Verify order: analyze -> plan -> decide -> generate -> assemble
    gen_idx = engine.call_order.index("generate")
    asm_idx = engine.call_order.index("assemble")
    assert gen_idx < asm_idx
