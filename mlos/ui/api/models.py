from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    workspaces = relationship("Workspace", back_populates="owner", foreign_keys="[Workspace.owner_id]")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)  # UUID token string
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="workspaces", foreign_keys=[owner_id])
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan")

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    workspace_id = Column(Integer, ForeignKey("workspaces.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role = Column(String, default="admin", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    project_name = Column(String, nullable=False)
    project_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="projects")
