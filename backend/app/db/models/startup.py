from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Startup(Base):
    __tablename__ = "startups"

    id = Column(Integer, primary_key=True, index=True)
    founder_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    startup_id = Column(String(100), unique=True, index=True, nullable=False)  # On-chain ID
    name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=False)
    country = Column(String(100), nullable=True)
    employees_verified = Column(Integer, default=0)
    credibility_score = Column(Float, default=0.0)
    transaction_signature = Column(String(88), nullable=True)
    funding_goal = Column(Float, nullable=True)  # Funding goal in USDC
    pitch_deck_url = Column(String(500), nullable=True)  # URL to pitch deck
    description = Column(String(2000), nullable=True)  # Startup description
    
    # Additional business information
    website = Column(String(500), nullable=True)  # Company website
    contact_email = Column(String(255), nullable=True)  # Contact email
    phone = Column(String(50), nullable=True)  # Contact phone
    address = Column(String(500), nullable=True)  # Business address
    year_founded = Column(Integer, nullable=True)  # Year the startup was founded
    team_size = Column(Integer, nullable=True)  # Current team size
    mission = Column(String(1000), nullable=True)  # Mission statement
    vision = Column(String(1000), nullable=True)  # Vision statement
    products_services = Column(String(2000), nullable=True)  # Key products/services
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    founder = relationship("User", back_populates="startups")
    jobs = relationship("Job", back_populates="startup")
    investments = relationship("Investment", back_populates="startup")

