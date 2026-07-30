"""
Unit and integration tests for the ML-OS CLI Subsystem.
"""
import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from rich.console import Console

from mlos.cli.main import main
from mlos.cli.command import BaseCommand
from mlos.cli.persistence import (
    find_project_root,
    load_project_config,
    save_project_config,
    reconstruct_project_memory,
)
from mlos.domain.models.analysis_report import AnalysisReport
from mlos.domain.models.dataset import Dataset
from mlos.domain.models.decision import Decision
from mlos.domain.models.recommendation import Recommendation
from mlos.domain.enums.recommendation_priority import RecommendationPriority
from mlos.domain.models.workflow_result import WorkflowResult
from datetime import datetime


def test_command_persistence_load_save(tmp_path):
    # Setup mock project structure in tmp_path
    project_dir = tmp_path / "MyProject"
    project_dir.mkdir()
    
    # Save a configuration
    config = {
        "project_name": "MyProject",
        "project_goal": "Goal description",
        "current_stage": "Analysis",
        "completed_tasks": ["task1"],
        "notes": ["note1"],
        "dataset_path": "data/dataset.csv",
        "target_column": "target",
    }
    save_project_config(project_dir, config)
    
    # Verify load
    loaded = load_project_config(project_dir)
    assert loaded == config
    
    # Reconstruct memory
    memory = reconstruct_project_memory(project_dir)
    assert memory.project_name == "MyProject"
    assert memory.project_goal == "Goal description"
    assert memory.current_stage == "Analysis"
    assert memory.completed_tasks == ["task1"]
    assert memory.notes == ["note1"]
    assert memory.dataset is not None
    assert memory.dataset.path == "data/dataset.csv"
    assert memory.dataset.target == "target"


def test_find_project_root(tmp_path, monkeypatch):
    # Setup mock folders
    project_dir = tmp_path / "ActiveProject"
    project_dir.mkdir()
    (project_dir / ".mlos").mkdir()
    sub_dir = project_dir / "data" / "sub"
    sub_dir.mkdir(parents=True)
    
    # Check parent search from sub_dir
    root = find_project_root(start_dir=sub_dir)
    assert root.resolve() == project_dir.resolve()
    
    # Check search when no .mlos folder exists
    empty_dir = tmp_path / "Empty"
    empty_dir.mkdir()
    assert find_project_root(start_dir=empty_dir) is None


@patch("mlos.cli.commands.init.save_project_config")
def test_cli_init_non_interactive_success(mock_save, tmp_path, monkeypatch):
    # Mock create_project of MLOSEngine to run without actual directory creation in tests
    with patch("mlos.engine.engine.MLOSEngine.create_project") as mock_create:
        # Patch playground path to map to tmp_path
        monkeypatch.chdir(tmp_path)
        exit_code = main(["init", "--name", "TestProject", "--goal", "Accuracy", "--non-interactive"])
        
        assert exit_code == 0
        mock_create.assert_called_once_with(name="TestProject", goal="Accuracy")
        mock_save.assert_called_once()


def test_cli_init_missing_args_error():
    exit_code = main(["init", "--non-interactive"])
    assert exit_code == 1


@patch("rich.prompt.Prompt.ask")
@patch("mlos.cli.commands.init.save_project_config")
def test_cli_init_interactive_success(mock_save, mock_ask, tmp_path, monkeypatch):
    # Mock interactive Prompt.ask
    mock_ask.side_effect = ["InteractiveProj", "InteractiveGoal"]
    
    with patch("mlos.engine.engine.MLOSEngine.create_project") as mock_create:
        monkeypatch.chdir(tmp_path)
        exit_code = main(["init"])
        
        assert exit_code == 0
        mock_create.assert_called_once_with(name="InteractiveProj", goal="InteractiveGoal")
        mock_save.assert_called_once()


@patch("mlos.cli.commands.analyze.find_project_root")
def test_cli_analyze_not_in_project(mock_find_root):
    mock_find_root.return_value = None
    exit_code = main(["analyze", "--dataset", "dummy.csv"])
    assert exit_code == 1


@patch("mlos.cli.commands.analyze.find_project_root")
@patch("mlos.cli.commands.analyze.reconstruct_project_memory")
def test_cli_analyze_success(mock_reconstruct, mock_find_root, tmp_path):
    project_dir = tmp_path / "MyProject"
    project_dir.mkdir()
    (project_dir / ".mlos").mkdir()
    mock_find_root.return_value = project_dir
    
    # Mock reconstructed memory
    from mlos.domain.models.project_memory import ProjectMemory
    memory = ProjectMemory(project_name="MyProject", project_goal="Goal description")
    mock_reconstruct.return_value = memory
    
    # Mock engine analysis
    mock_report = AnalysisReport(
        dataset=Dataset(
            path="dummy.csv",
            rows=100,
            columns=5,
            target="label",
            problem_type="Classification",
            categorical_columns=["col1"],
            numerical_columns=["col2"],
            missing_values={},
            duplicate_rows=0,
            unique_values={},
            missing_percentages={},
            column_types={},
        ),
        decisions=[
            Decision(title="Imputation", strategy="mean", confidence="High", reason="missing data")
        ],
        recommendations=[
            Recommendation(title="Scale numericals", description="Use StandardScaler", priority=RecommendationPriority.MEDIUM)
        ],
    )
    
    with patch("mlos.engine.engine.MLOSEngine.run_analysis", return_value=mock_report) as mock_run_analysis:
        exit_code = main(["analyze", "--dataset", "dummy.csv", "--target", "label"])
        assert exit_code == 0
        mock_run_analysis.assert_called_once_with("dummy.csv", "label")


@patch("mlos.cli.commands.run.find_project_root")
@patch("mlos.cli.commands.run.reconstruct_project_memory")
def test_cli_run_success(mock_reconstruct, mock_find_root, tmp_path):
    project_dir = tmp_path / "MyProject"
    project_dir.mkdir()
    (project_dir / ".mlos").mkdir()
    mock_find_root.return_value = project_dir
    
    # Mock reconstructed memory
    from mlos.domain.models.project_memory import ProjectMemory
    memory = ProjectMemory(project_name="MyProject", project_goal="Goal description")
    mock_reconstruct.return_value = memory
    
    # Mock engine workflow run
    mock_result = WorkflowResult(
        status="SUCCESS",
        start_time=datetime.now(),
        end_time=datetime.now(),
    )
    
    with patch("mlos.engine.engine.MLOSEngine.run", return_value=mock_result) as mock_run:
        exit_code = main(["run", "--dataset", "dummy.csv", "--target", "label"])
        assert exit_code == 0
        mock_run.assert_called_once_with("dummy.csv", "label")


def test_cli_doctor_output():
    # Verify doctor runs and prints exit code 0 when all packages are installed
    exit_code = main(["doctor"])
    assert exit_code == 0
