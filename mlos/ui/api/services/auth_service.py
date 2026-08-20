import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import VerifyMismatchError
from .. import models, schemas

class PasswordHasher:
    """
    Argon2id implementation of the password-hashing abstraction.
    """
    def __init__(self):
        self.ph = Argon2Hasher()

    def hash(self, password: str) -> str:
        return self.ph.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        try:
            return self.ph.verify(hashed, password)
        except VerifyMismatchError:
            return False

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.hasher = PasswordHasher()

    def create_user(self, user_in: schemas.UserCreate) -> models.User:
        hashed_password = self.hasher.hash(user_in.password)
        db_user = models.User(
            email=user_in.email,
            password_hash=hashed_password
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def authenticate_user(self, email: str, password: str) -> models.User | None:
        user = self.db.query(models.User).filter(models.User.email == email).first()
        if not user:
            return None
        if not self.hasher.verify(password, user.password_hash):
            return None
        return user

    def create_session(self, user_id: int, expires_in_days: int = 7) -> models.Session:
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        db_session = models.Session(
            id=session_id,
            user_id=user_id,
            expires_at=expires_at
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def get_session(self, session_id: str) -> models.Session | None:
        session = self.db.query(models.Session).filter(models.Session.id == session_id).first()
        if not session:
            return None
        if session.expires_at < datetime.utcnow():
            # Session expired, delete it
            self.db.delete(session)
            self.db.commit()
            return None
        return session

    def delete_session(self, session_id: str) -> None:
        session = self.db.query(models.Session).filter(models.Session.id == session_id).first()
        if session:
            self.db.delete(session)
            self.db.commit()
