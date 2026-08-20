import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Ensure ~/.mlos directory exists for platform configurations
db_dir = Path.home() / ".mlos"
db_dir.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{db_dir}/mlos_platform.db"

# Create SQLAlchemy connection engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite multi-threading
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency provider yielding SQLAlchemy local database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
