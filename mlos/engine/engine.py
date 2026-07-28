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

        if self.memory is None:
            raise RuntimeError(
              "Create a project before analyzing a dataset."
          )

        dataframe = self.data_loader.load(dataset_path)

        dataset = self.dataset_analyzer.analyze(dataframe)

        self.project_memory_service.update_dataset(
          self.memory,
          dataset,
      )

    def reason(self):
        """Reason about the current project."""
        raise NotImplementedError

    def plan(self):
        """Generate a plan for the current project."""

        return self.planner.create_plan()

    def generate(self):
        """Generate code for the next step."""
        raise NotImplementedError

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
