"""
Planning Engine.

Generates the execution plan for ML projects.

Author: Vikram Tanakala
License: MIT
"""

from mlos.domain.models.task import Task


class PlanningEngine:
    """
    Generates task plans for ML projects.
    """

    def create_plan(self) -> list[Task]:
        """
        Generate the default Quick Challenge workflow.
        """
        print("PlanningEngine.create_plan() called")
        return [

            Task(
                id="TASK-001",
                title="Understand the Problem",
                description="Understand the business objective.",
            ),

            Task(
                id="TASK-002",
                title="Inspect Dataset",
                description="Analyze dataset structure.",
                depends_on=["TASK-001"],
            ),

            Task(
                id="TASK-003",
                title="Identify Target",
                description="Determine prediction target.",
                depends_on=["TASK-002"],
            ),

            Task(
                id="TASK-004",
                title="Analyze Missing Values",
                description="Inspect missing values.",
                depends_on=["TASK-003"],
            ),

            Task(
                id="TASK-005",
                title="Generate Baseline Model",
                description="Train the first model.",
                depends_on=["TASK-004"],
            ),

            Task(
                id="TASK-006",
                title="Evaluate Model",
                description="Evaluate model performance.",
                depends_on=["TASK-005"],
            ),

        ]