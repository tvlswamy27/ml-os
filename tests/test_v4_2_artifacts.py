import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import os
import json

from mlos.ui.api.main import app
from mlos.ui.api.database import Base, engine, get_db
from mlos.ui.api import models

# Testing dependencies
from mlos.ui.api.routers.auth import get_current_user

# Mock user for testing
def override_get_current_user():
    return models.User(id=1, email="test@example.com")

@pytest.fixture(autouse=True)
def override_auth():
    old = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    if old:
        app.dependency_overrides[get_current_user] = old
    else:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(scope="module")
def client():
    # Set up database schema
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def setup_test_project(client, tmp_path):
    # Setup test workspace and project in db
    db = next(get_db())
    # Create user
    user = models.User(id=1, email="test@example.com", password_hash="pw")
    db.merge(user)
    db.commit()
    
    workspace = models.Workspace(id=1, name="Test WS", owner_id=1)
    db.merge(workspace)
    db.commit()
    
    member = models.WorkspaceMember(workspace_id=1, user_id=1, role="admin")
    db.merge(member)
    db.commit()
    
    proj_dir = tmp_path / "test_proj"
    proj_dir.mkdir(parents=True, exist_ok=True)
    
    project = models.Project(id=1, workspace_id=1, project_name="Test Proj", project_path=str(proj_dir))
    db.merge(project)
    db.commit()
    
    return proj_dir

def test_unauthenticated_listing():
    app.dependency_overrides.pop(get_current_user, None)
    c = TestClient(app)
    response = c.get("/api/projects/1/artifacts")
    assert response.status_code == 401

def test_unauthenticated_download():
    app.dependency_overrides.pop(get_current_user, None)
    c = TestClient(app)
    response = c.get("/api/projects/1/artifacts/download?path=pipeline.py")
    assert response.status_code == 401

def test_unauthorized_project(client, setup_test_project):
    # User 1 tries to access project 99
    response = client.get("/api/projects/99/artifacts")
    assert response.status_code == 404

def test_empty_artifacts(client, setup_test_project):
    response = client.get("/api/projects/1/artifacts")
    assert response.status_code == 200
    assert response.json() == []

def test_artifact_listing(client, setup_test_project):
    proj_dir = setup_test_project
    (proj_dir / "pipeline.py").write_text("print('hello')", encoding="utf-8")
    (proj_dir / "model.joblib").write_text("modeldata", encoding="utf-8")
    
    art_dir = proj_dir / "artifacts"
    art_dir.mkdir(exist_ok=True)
    (art_dir / "test.txt").write_text("some data", encoding="utf-8")
    
    response = client.get("/api/projects/1/artifacts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    names = [a["name"] for a in data]
    assert "pipeline.py" in names
    assert "model.joblib" in names
    assert "test.txt" in names

def test_authenticated_download(client, setup_test_project):
    proj_dir = setup_test_project
    (proj_dir / "pipeline.py").write_text("print('hello')", encoding="utf-8")
    
    response = client.get("/api/projects/1/artifacts/download?path=pipeline.py")
    assert response.status_code == 200
    assert response.text == "print('hello')"

def test_missing_artifact(client, setup_test_project):
    response = client.get("/api/projects/1/artifacts/download?path=metrics.json")
    assert response.status_code == 404

def test_arbitrary_root_file_rejected(client, setup_test_project):
    proj_dir = setup_test_project
    (proj_dir / "secret.txt").write_text("secret", encoding="utf-8")
    
    response = client.get("/api/projects/1/artifacts/download?path=secret.txt")
    assert response.status_code == 403

def test_path_traversal_rejected(client, setup_test_project):
    response = client.get("/api/projects/1/artifacts/download?path=../../etc/passwd")
    assert response.status_code == 400

def test_windows_traversal_rejected(client, setup_test_project):
    response = client.get("/api/projects/1/artifacts/download?path=..\\..\\Windows\\System32\\cmd.exe")
    assert response.status_code == 400

def test_absolute_path_rejected(client, setup_test_project):
    response = client.get("/api/projects/1/artifacts/download?path=/etc/passwd")
    assert response.status_code == 400
    
    response = client.get("/api/projects/1/artifacts/download?path=C:/Windows/System32/cmd.exe")
    assert response.status_code == 400

def test_directory_download_rejected(client, setup_test_project):
    proj_dir = setup_test_project
    art_dir = proj_dir / "artifacts"
    art_dir.mkdir(exist_ok=True)
    
    response = client.get("/api/projects/1/artifacts/download?path=artifacts")
    assert response.status_code == 403
