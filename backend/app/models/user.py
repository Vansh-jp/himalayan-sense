import uuid
from sqlalchemy import Column, String, Uuid
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(30), nullable=True)
    role = Column(String(20), default="citizen", nullable=False)  # citizen | admin
    district = Column(String(100), nullable=True, default="Dehradun")

    # Relationships
    incidents = relationship("Incident", back_populates="user", cascade="all, delete-orphan")
