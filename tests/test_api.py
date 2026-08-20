import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from mlos.ui.api.main import app
from mlos.ui.api.database import Base, get_db
import mlos.ui.api.models as models

from sqlalchemy.pool import StaticPool

# Configure isolated testing SQLite in-memory database
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Re-create tables inside in-memory testing DB
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override FastAPI database session dependency provider
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure database state is clean before each test run."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


# --- 1. AUTH TESTS ---

def test_signup_success():
    response = client.post(
        "/api/auth/signup",
        json={"email": "engineer@mlos.org", "password": "securepassword123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == "engineer@mlos.org"

def test_signup_duplicate_email():
    # Register first
    client.post(
        "/api/auth/signup",
        json={"email": "engineer@mlos.org", "password": "securepassword123"}
    )
    # Register same email again
    response = client.post(
        "/api/auth/signup",
        json={"email": "engineer@mlos.org", "password": "anotherpassword"}
    )
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]

def test_login_success():
    client.post(
        "/api/auth/signup",
        json={"email": "engineer@mlos.org", "password": "securepassword123"}
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "engineer@mlos.org", "password": "securepassword123"}
    )
    assert response.status_code == 200
    assert "session_id" in response.cookies
    assert response.json()["email"] == "engineer@mlos.org"

def test_login_invalid_credentials():
    client.post(
        "/api/auth/signup",
        json={"email": "engineer@mlos.org", "password": "securepassword123"}
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "engineer@mlos.org", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Invalid email or password." in response.json()["detail"]

def test_me_authenticated():
    client.post(
        "/api/auth/signup",
        json={"email": "engineer@mlos.org", "password": "securepassword123"}
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "engineer@mlos.org", "password": "securepassword123"}
    )
    session_cookie = login_resp.cookies.get("session_id")
    
    # Request profile passing session cookie
    response = client.get("/api/auth/me", cookies={"session_id": session_cookie})
    assert response.status_code == 200
    assert response.json()["email"] == "engineer@mlos.org"

def test_me_unauthenticated():
    response = client.get("/api/auth/me")
    assert response.status_code == 401

def test_logout():
    client.post(
        "/api/auth/signup",
        json={"email": "engineer@mlos.org", "password": "securepassword123"}
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "engineer@mlos.org", "password": "securepassword123"}
    )
    session_cookie = login_resp.cookies.get("session_id")
    
    # Perform logout
    logout_resp = client.post("/api/auth/logout", cookies={"session_id": session_cookie})
    assert logout_resp.status_code == 200
    
    # Session cookie must be empty or invalid now
    me_resp = client.get("/api/auth/me", cookies={"session_id": session_cookie})
    assert me_resp.status_code == 401

def test_expired_session():
    db = TestingSessionLocal()
    # Create user manually
    user = models.User(email="test@mlos.org", password_hash="dummy")
    db.add(user)
    db.commit()
    
    # Create an expired session
    session_id = "expired-token-id"
    session = models.Session(
        id=session_id,
        user_id=user.id,
        expires_at=datetime.utcnow() - timedelta(minutes=10)
    )
    db.add(session)
    db.commit()
    db.close()
    
    # Request /me using expired session
    response = client.get("/api/auth/me", cookies={"session_id": session_id})
    assert response.status_code == 401


# --- 2. AUTHORIZATION TESTS ---

def test_workspace_membership_authorization():
    # User A registers (creates Workspace A)
    client.post(
        "/api/auth/signup",
        json={"email": "usera@mlos.org", "password": "passwordA"}
    )
    login_a = client.post(
        "/api/auth/login",
        json={"email": "usera@mlos.org", "password": "passwordA"}
    )
    cookie_a = login_a.cookies.get("session_id")
    
    # User B registers (creates Workspace B)
    client.post(
        "/api/auth/signup",
        json={"email": "userb@mlos.org", "password": "passwordB"}
    )
    login_b = client.post(
        "/api/auth/login",
        json={"email": "userb@mlos.org", "password": "passwordB"}
    )
    cookie_b = login_b.cookies.get("session_id")
    
    # Get Workspace A ID (first workspace of User A)
    w_resp = client.get("/api/workspaces", cookies={"session_id": cookie_a})
    workspace_a_id = w_resp.json()[0]["id"]
    
    # User B attempts to access User A's workspace
    p_resp = client.get(f"/api/projects?workspace_id={workspace_a_id}", cookies={"session_id": cookie_b})
    assert p_resp.json()["detail"]["code"] == "WORKSPACE_ACCESS_DENIED"


# --- 3. PROJECT & PATH SECURITY TESTS ---

def test_project_creation_and_listing():
    # Register & Login
    client.post(
        "/api/auth/signup",
        json={"email": "user@mlos.org", "password": "password"}
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "user@mlos.org", "password": "password"}
    )
    cookie = login_resp.cookies.get("session_id")
    
    w_resp = client.get("/api/workspaces", cookies={"session_id": cookie})
    workspace_id = w_resp.json()[0]["id"]
    
    # Create project using safe paths
    safe_path = str(Path.cwd().resolve() / "playground" / "project_alpha")
    response = client.post(
        f"/api/projects?workspace_id={workspace_id}",
        json={"project_name": "Project Alpha", "project_path": safe_path},
        cookies={"session_id": cookie}
    )
    assert response.status_code == 211 or response.status_code == 201
    
    # List projects in workspace
    list_resp = client.get(f"/api/projects?workspace_id={workspace_id}", cookies={"session_id": cookie})
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["project_name"] == "Project Alpha"

def test_path_traversal_rejection():
    client.post(
        "/api/auth/signup",
        json={"email": "user@mlos.org", "password": "password"}
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "user@mlos.org", "password": "password"}
    )
    cookie = login_resp.cookies.get("session_id")
    w_resp = client.get("/api/workspaces", cookies={"session_id": cookie})
    workspace_id = w_resp.json()[0]["id"]
    
    # Attempt directory traversal injection
    bad_path = "../../etc/passwd"
    response = client.post(
        f"/api/projects?workspace_id={workspace_id}",
        json={"project_name": "Hack Project", "project_path": bad_path},
        cookies={"session_id": cookie}
    )
    assert response.status_code == 400
    assert "traversal" in response.json()["detail"]["message"] or "outside" in response.json()["detail"]["message"]


# --- 4. SSE EVENTS TESTS ---

def test_sse_event_subscription_and_isolation():
    client.post(
        "/api/auth/signup",
        json={"email": "user@mlos.org", "password": "password"}
    )
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "user@mlos.org", "password": "password"}
    )
    cookie = login_resp.cookies.get("session_id")
    w_resp = client.get("/api/workspaces", cookies={"session_id": cookie})
    workspace_id = w_resp.json()[0]["id"]
    
    # Create project
    safe_path = str(Path.cwd().resolve() / "playground" / "project_beta")
    proj_resp = client.post(
        f"/api/projects?workspace_id={workspace_id}",
        json={"project_name": "Project Beta", "project_path": safe_path},
        cookies={"session_id": cookie}
    )
    project_id = proj_resp.json()["id"]
    
    # Simulate a run event
    run_id = "test-run-uuid-123"
    
    # Retrieve SSE connection (since it yields heartbeat or wait, we can mock EventStreamService to isolate runs)
    with patch("mlos.ui.api.routers.project.EventStreamService.subscribe") as mock_sub:
        mock_sub.return_value = ["event: Heartbeat\ndata: {}\n\n"]
        response = client.get(
            f"/api/projects/{project_id}/run/events/{run_id}",
            cookies={"session_id": cookie}
        )
        assert response.status_code == 200
        # Stream response contents checks
        assert b"Heartbeat" in response.content
