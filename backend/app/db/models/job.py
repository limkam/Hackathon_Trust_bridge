from sqlalchemy import Column, Integer, String, ForeignKey, ARRAY, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    startup_id = Column(Integer, ForeignKey("startups.id"), nullable=True)  # Optional for non-startup companies
    company_name = Column(String(255), nullable=True)  # For non-startup companies
    title = Column(String(255), nullable=False)
    description = Column(String(2000), nullable=False)
    location = Column(String(255), nullable=False)
    skills_required = Column(ARRAY(String), nullable=False)
    min_experience = Column(Integer, default=0)  # Years
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    startup = relationship("Startup", back_populates="jobs")
    matches = relationship("JobMatch", back_populates="job")
    applications = relationship("JobApplication", back_populates="job")

