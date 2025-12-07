from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class CV(Base):
    __tablename__ = "cvs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    json_content = Column(JSON, nullable=False)  # Full CV data as JSON
    ai_score = Column(Float, nullable=True)  # AI-generated quality score
    photo_url = Column(String(500), nullable=True)  # URL/path to user photo
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="cvs")
    applications = relationship("JobApplication", back_populates="cv")

