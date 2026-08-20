from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import schemas, models
from ..services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])

def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    """Dependency that extracts the session cookie, checks validity, and returns the User."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated."
        )
    auth_service = AuthService(db)
    session = auth_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid."
        )
    user = db.query(models.User).filter(models.User.id == session.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found."
        )
    return user

@router.post("/signup", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    # Check if duplicate email
    existing_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address already registered."
        )
    try:
        user = auth_service.create_user(user_in)
        # Create a default workspace for this user
        db_workspace = models.Workspace(name="Default Workspace", owner_id=user.id)
        db.add(db_workspace)
        db.commit()
        db.refresh(db_workspace)
        
        # Add as administrator member
        db_member = models.WorkspaceMember(workspace_id=db_workspace.id, user_id=user.id, role="admin")
        db.add(db_member)
        db.commit()
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login")
def login(credentials: schemas.UserLogin, response: Response, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    session = auth_service.create_session(user.id)
    
    # Store session in HttpOnly cookie
    response.set_cookie(
        key="session_id",
        value=session.id,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to False to support dev localhost HTTP
        max_age=7 * 24 * 3600  # 7 days
    )
    return {"message": "Successfully authenticated.", "email": user.email}

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    if session_id:
        auth_service = AuthService(db)
        auth_service.delete_session(session_id)
    response.delete_cookie("session_id")
    return {"message": "Successfully logged out."}

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
