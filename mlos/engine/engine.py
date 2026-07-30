"""
ML-OS Engine.

Main orchestrator for ML-OS.

Author: Vikram Tanakala
License: MIT
"""
from mlos.planning.planner import PlanningEngine
from mlos.domain.services.workspace_service import WorkspaceService
from mlos.domain.services.project_service import ProjectService
from mlos.io.data_loader import DataLoader
from mlos.analysis.dataset_analyzer import DatasetAnalyzer
from mlos.domain.services.project_memory_service import (
    ProjectMemoryService,
)
from mlos.decision.decision_engine import DecisionEngine
from mlos.domain.models.analysis_report import AnalysisReport
from mlos.reasoning.reasoning_engine import ReasoningEngine
from mlos.generator.generator_engine import GeneratorEngine
from mlos.intelligence.intelligence_engine import IntelligenceEngine
from mlos.execution.execution_engine import ExecutionEngine
from mlos.execution.runners.local_runner import LocalProcessPipelineRunner
from mlos.domain.services.execution_service import ExecutionService
from mlos.generator.assembler.code_assembler import CodeAssembler
from mlos.generator.assembler.pipeline_assembly_engine import PipelineAssemblyEngine
from mlos.domain.services.assembly_service import AssemblyService
from mlos.domain.models.generated_code import GeneratedCode
from mlos.evaluation.evaluation_engine import EvaluationEngine
from mlos.evaluation.evaluators.simple_evaluator import SimpleEvaluator
from mlos.domain.services.evaluation_service import EvaluationService
from mlos.workflow.workflow_engine import WorkflowEngine
from mlos.workflow.workflow_hooks import HookRegistry
from mlos.domain.models.workflow_result import WorkflowResult

class MLOSEngine:
    """
    Main entry point for ML-OS.
    """

    def __init__(self):
        self.workspace_service = WorkspaceService()
        self.project_service = ProjectService()
        self.planner = PlanningEngine()
        self.data_loader = DataLoader()
        self.dataset_analyzer = DatasetAnalyzer()
        self.project_memory_service = ProjectMemoryService()
        self.decision_engine = DecisionEngine()
        self.reasoning_engine = ReasoningEngine()
        self.generator_engine = GeneratorEngine()
        self.intelligence_engine = IntelligenceEngine()
        self.execution_engine = ExecutionEngine(LocalProcessPipelineRunner())
        self.execution_service = ExecutionService(
            self.execution_engine,
            self.project_memory_service,
        )
        self.assembly_engine = PipelineAssemblyEngine(CodeAssembler())
        self.assembly_service = AssemblyService(
            self.assembly_engine,
            self.project_memory_service,
        )
        self.evaluation_engine = EvaluationEngine()
        self.evaluation_engine.register_evaluator(SimpleEvaluator())
        self.evaluation_service = EvaluationService(
            self.evaluation_engine,
            self.project_memory_service,
        )
        self.hooks = HookRegistry()
        self.workflow_engine = WorkflowEngine(self, self.hooks)
        self.project_memory = None

    def create_project(
        self,
        name: str,
        goal: str,
   ):  
        """
      Create a new project.
      """

        project_path = self.project_service.create_project(name)

        self.project_memory = self.project_memory_service.create(
            project_name=name,
            project_goal=goal,
        )

        print(f"Project created at: {project_path}")

    def open_project(self):
        """Open an existing ML project."""
        raise NotImplementedError

    def analyze(
        self,
        dataset_path: str,
   ):
        """
      Analyze a dataset.
      """

        if self.project_memory is None:
            raise RuntimeError(
              "Create a project before analyzing a dataset."
          )

        dataframe = self.data_loader.load(dataset_path)

        dataset = self.dataset_analyzer.analyze(dataframe)
        dataset.path = dataset_path

        self.project_memory_service.update_dataset(
                  self.project_memory,
                  dataset,   
              )

        profile = self.intelligence_engine.analyze(
            self.project_memory,
        )

        self.project_memory.profile = profile

        

    def reason(self):
        """Reason about the current project."""
        raise NotImplementedError

    def plan(self):
        """Generate a plan for the current project."""

        return self.planner.create_plan()

    def generate(self):
        """Generate code for the next step."""
        raise NotImplementedError

    def execute(self):
        """Execute the generated pipeline."""
        if self.project_memory is None:
            raise RuntimeError(
                "Create or load a project before running execution."
            )
        self.execution_service.run_execution(self.project_memory)

    def assemble(self, generated_codes: list[GeneratedCode]) -> None:
        """Assemble transient GeneratedCode blocks into a Pipeline."""
        if self.project_memory is None:
            raise RuntimeError(
                "Create or load a project before running assembly."
            )
        self.assembly_service.run_assembly(self.project_memory, generated_codes)

    def evaluate(self) -> None:
        """Evaluate the execution outputs of the pipeline."""
        if self.project_memory is None:
            raise RuntimeError(
                "Create or load a project before running evaluation."
            )
        self.evaluation_service.run_evaluation(self.project_memory)

    def run(self, dataset_path: str, target: str | None = None) -> WorkflowResult:
        """
        Executes the complete machine learning engineering lifecycle automatically.
        """
        if self.project_memory is None:
            raise RuntimeError(
                "Create or load a project before running a workflow."
            )
        return self.workflow_engine.run(dataset_path, target)

    def explain(self):
        """Explain ML-OS decisions."""
        raise NotImplementedError

    def get_memory(self):
        """
      Return the current project memory.
      """

        return self.project_memory

    def run_analysis(
        self,
        dataset_path: str,
        target: str | None = None,
    ) -> AnalysisReport:
        """
        Run the full analysis pipeline on a dataset.
        """

        if self.project_memory is None:
            raise RuntimeError(
              "Create a project before analyzing a dataset."
          )

        dataframe = self.data_loader.load(dataset_path)

        dataset = self.dataset_analyzer.analyze(dataframe)
        dataset.target = target

        self.project_memory_service.update_dataset(
            self.project_memory,
            dataset,
        )

        profile = self.intelligence_engine.analyze(
            self.project_memory,
        )

        self.project_memory.profile = profile
        
        decisions = self.decision_engine.decide(
            self.project_memory,
        )

        recommendations = self.reasoning_engine.reason(
            self.project_memory,
        )

        return AnalysisReport(
            dataset=dataset,
            decisions=decisions,
            recommendations=recommendations,
        )
