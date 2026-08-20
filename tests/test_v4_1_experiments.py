import pytest
from dataclasses import asdict
from pathlib import Path
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from mlos.experiment.tracker import ExperimentTracker, ExperimentRecord, ExperimentTrial
from mlos.ui.api.main import app
from mlos.ui.api.database import Base, get_db
import mlos.ui.api.models as models

# Configure isolated testing database
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def override_database_dependency():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_experiment_trial_serialization():
    trial = ExperimentTrial(
        trial_id="t-1",
        model_name="RandomForest",
        estimator_class="sklearn.ensemble.RandomForestClassifier",
        metric="accuracy",
        score=0.95,
        cv_mean=0.95,
        cv_std=0.01,
        cv_scores=[0.94, 0.96],
        parameters={"n_estimators": 100},
        rank=1,
        status="SUCCESS",
        selected=True,
        duration_seconds=0.5,
    )
    d = asdict(trial)
    assert d["trial_id"] == "t-1"
    assert d["parameters"]["n_estimators"] == 100
    assert d["cv_scores"] == [0.94, 0.96]

def test_experiment_record_backward_compatibility(tmp_path):
    # Save old-style experiments json (no candidate_trials)
    old_data = {
        "exp-1": {
            "experiment_id": "exp-1",
            "name": "exp-1",
            "timestamp": "2026-08-20T10:00:00Z",
            "dataset_fingerprint": "fingerprint123",
            "problem_type": "binary_classification",
            "pipeline_id": "pipe-1",
            "selected_model": "RandomForest",
            "candidate_models": ["RandomForest"],
            "hyperparameters": {},
            "metrics": {"accuracy": 0.92},
            "cv_scores": [0.92],
            "training_time_s": 0.5,
            "prediction_time_s": 0.01,
            "memory_usage_mb": 50.0,
            "feature_importance": {},
            "artifacts": {},
            "environment": {},
            "status": "SUCCESS"
        }
    }
    experiments_file = tmp_path / ".mlos" / "experiments" / "experiments.json"
    experiments_file.parent.mkdir(parents=True, exist_ok=True)
    experiments_file.write_text(json.dumps(old_data), encoding="utf-8")

    tracker = ExperimentTracker(tmp_path)
    records = tracker.list_experiments()
    assert len(records) == 1
    assert records[0]["experiment_id"] == "exp-1"
    assert "candidate_trials" not in records[0] or records[0]["candidate_trials"] == []

def test_multiple_candidates_persistence_and_ranking(tmp_path):
    tracker = ExperimentTracker(tmp_path)
    
    trials = [
        ExperimentTrial(
            trial_id="t-rf",
            model_name="Random Forest",
            estimator_class="sklearn.ensemble.RandomForestClassifier",
            metric="accuracy",
            score=0.95,
            cv_mean=0.95,
            cv_std=0.01,
            cv_scores=[0.94, 0.96],
            parameters={"n_estimators": 100},
            rank=1,
            status="SUCCESS",
            selected=True,
            duration_seconds=0.5
        ),
        ExperimentTrial(
            trial_id="t-lr",
            model_name="Logistic Regression",
            estimator_class="sklearn.linear_model.LogisticRegression",
            metric="accuracy",
            score=0.91,
            cv_mean=0.91,
            cv_std=0.02,
            cv_scores=[0.89, 0.93],
            parameters={"C": 1.0},
            rank=2,
            status="SUCCESS",
            selected=False,
            duration_seconds=0.2
        ),
        ExperimentTrial(
            trial_id="t-fail",
            model_name="Extra Trees",
            estimator_class="sklearn.ensemble.ExtraTreesClassifier",
            metric="accuracy",
            score=0.0,
            cv_mean=0.0,
            cv_std=0.0,
            cv_scores=[],
            parameters={},
            rank=3,
            status="FAILED",
            selected=False,
            duration_seconds=0.1,
            error="Mock failure exception"
        )
    ]
    
    rec = tracker.log_experiment(
        dataset_fingerprint="fp-123",
        problem_type="binary_classification",
        pipeline_id="pipe-rf",
        selected_model="Random Forest",
        candidate_models=["Random Forest", "Logistic Regression", "Extra Trees"],
        metrics={"accuracy": 0.95},
        cv_scores=[0.94, 0.96],
        training_time_s=0.5,
        prediction_time_s=0.01,
        memory_usage_mb=50.0,
        feature_importance={},
        artifacts={},
        hyperparameters={"n_estimators": 100},
        candidate_trials=trials
    )
    
    fetched = tracker.get_experiment(rec.experiment_id)
    assert fetched is not None
    assert len(fetched["candidate_trials"]) == 3
    assert fetched["candidate_trials"][0]["model_name"] == "Random Forest"
    assert fetched["candidate_trials"][0]["selected"] is True
    assert fetched["candidate_trials"][1]["rank"] == 2
    assert fetched["candidate_trials"][2]["status"] == "FAILED"
    assert fetched["candidate_trials"][2]["error"] == "Mock failure exception"

def test_api_empty_response(tmp_path, test_client):
    # Setup project in DB
    db = TestingSessionLocal()
    user = models.User(email="api@mlos.org", password_hash="dummy")
    db.add(user)
    db.commit()
    
    workspace = models.Workspace(name="API WS", owner_id=user.id)
    db.add(workspace)
    db.commit()
    
    member = models.WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="admin")
    db.add(member)
    db.commit()
    
    project = models.Project(
        workspace_id=workspace.id,
        project_name="API Proj",
        project_path=str(tmp_path)
    )
    db.add(project)
    db.commit()
    
    project_id = project.id
    
    session = models.Session(id="test-session-id", user_id=user.id, expires_at=datetime.utcnow() + timedelta(days=1))
    db.add(session)
    db.commit()
    db.close()
    
    # Request experiments (should be empty array)
    response = test_client.get(
        f"/api/projects/{project_id}/experiments",
        cookies={"session_id": "test-session-id"}
    )
    assert response.status_code == 200
    assert response.json() == []

def test_api_unauthorized_and_forbidden(tmp_path, test_client):
    # Request without session
    resp = test_client.get(f"/api/projects/1/experiments")
    assert resp.status_code == 401
    
    # Setup project
    db = TestingSessionLocal()
    user_a = models.User(email="a@mlos.org", password_hash="dummy")
    user_b = models.User(email="b@mlos.org", password_hash="dummy")
    db.add(user_a)
    db.add(user_b)
    db.commit()
    
    workspace_a = models.Workspace(name="WS A", owner_id=user_a.id)
    db.add(workspace_a)
    db.commit()
    
    member_a = models.WorkspaceMember(workspace_id=workspace_a.id, user_id=user_a.id, role="admin")
    db.add(member_a)
    db.commit()
    
    project_a = models.Project(
        workspace_id=workspace_a.id,
        project_name="Proj A",
        project_path=str(tmp_path)
    )
    db.add(project_a)
    db.commit()
    
    project_a_id = project_a.id
    
    session_b = models.Session(id="session-b-id", user_id=user_b.id, expires_at=datetime.utcnow() + timedelta(days=1))
    db.add(session_b)
    db.commit()
    db.close()
    
    # User B requests project A (forbidden)
    resp = test_client.get(
        f"/api/projects/{project_a_id}/experiments",
        cookies={"session_id": "session-b-id"}
    )
    assert resp.status_code == 403
