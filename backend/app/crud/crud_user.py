from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user(db: Session, user_id: UUID) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email.ilike(email.strip())).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    user = User(
        name=user_in.name.strip(),
        email=user_in.email.strip().lower(),
        password_hash=hash_password(user_in.password),
        phone=user_in.phone.strip() if user_in.phone else None,
        role=user_in.role or "citizen",
        district=user_in.district or "Dehradun",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def update_user(db: Session, db_user: User, user_in: UserUpdate) -> User:
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user
