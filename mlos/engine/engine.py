"""
ML-OS Engine.

Main orchestrator for ML-OS.

Author: Vikram Tanakala
License: MIT
"""
from mlos.planning.planner import PlanningEngine
from mlos.domain.services.workspace_service import WorkspaceService
from mlos.domain.services.project_service import ProjectService
class MLOSEngine:
    """
    Main entry point for ML-OS.
    """

    def __init__(self):
        self.workspace_service = WorkspaceService()
        self.project_service = ProjectService()
        self.planner = PlanningEngine()

    def create_project(
        self,
        name: str,
        goal: str,
   ):
        """
        Create a new ML project.
        """

        project_path = self.project_service.create_project(name)

        print(f"Project created at: {project_path}")

        print(f"Goal: {goal}")

        return project_path

    def open_project(self):
        """Open an existing ML project."""
        raise NotImplementedError

    def analyze(self):
        """Analyze the current project."""
        raise NotImplementedError

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