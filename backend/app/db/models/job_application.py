from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cv_id = Column(Integer, ForeignKey("cvs.id"), nullable=True)  # Reference to user's CV
    cover_letter = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending, reviewed, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="applications")
    user = relationship("User", back_populates="job_applications")
    cv = relationship("CV", back_populates="applications")

