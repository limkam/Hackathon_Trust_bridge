"""
CV Generator Module
Handles CV generation with AI enhancements, ATS optimization, and PDF/Word export.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# Add backend/app to path for imports
backend_dir = Path(__file__).parent.parent
app_dir = backend_dir / "app"
sys.path.insert(0, str(app_dir))

from services.ai_service import AIService
from db.models import CV, User
from utils.logger import logger
import json


class CVGenerator:
    """CV generation service with AI enhancements."""
    
    def __init__(self):
        self.ai_service = AIService()
    
    def generate_cv_with_market_analysis(
        self,
        user_id: int,
        personal_info: Dict[str, Any],
        experience: List[Dict[str, Any]],
        education: List[Dict[str, Any]],
        skills: Dict[str, Any],
        industry: Optional[str] = None,
        awards: List[Dict[str, Any]] = None,
        publications: List[Dict[str, Any]] = None,
        projects: List[Dict[str, Any]] = None,
        memberships: List[Dict[str, Any]] = None,
        job_id: Optional[int] = None,
        photo_url: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Generate CV with market analysis FIRST, then AI enhancements.
        This ensures suggestions are based on real market trends.
        """
        logger.info(f"Generating CV with market analysis for user {user_id}")
        
        # STEP 1: Analyze job market for the user's industry
        market_analysis = {}
        if db and industry:
            market_analysis = self.ai_service.analyze_job_market(db, sector=industry)
            logger.info(f"Market analysis: {len(market_analysis.get('trending_skills', []))} trending skills identified")
        
        # STEP 2: Generate CV (now informed by market analysis)
        cv_result = self.generate_cv(
            user_id=user_id,
            personal_info=personal_info,
            experience=experience,
            education=education,
            skills=skills,
            awards=awards,
            publications=publications,
            projects=projects,
            memberships=memberships,
            job_id=job_id,
            photo_url=photo_url,
            db=db
        )
        
        # STEP 3: Add market analysis to CV result
        cv_result["market_analysis"] = market_analysis
        
        return cv_result
    
    def generate_cv(
        self,
        user_id: int,
        personal_info: Dict[str, Any],
        experience: List[Dict[str, Any]],
        education: List[Dict[str, Any]],
        skills: Dict[str, Any],
        awards: List[Dict[str, Any]] = None,
        publications: List[Dict[str, Any]] = None,
        projects: List[Dict[str, Any]] = None,
        memberships: List[Dict[str, Any]] = None,
        job_id: Optional[int] = None,
        photo_url: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Generate a professional CV with AI enhancements.
        
        Args:
            user_id: User ID
            personal_info: Personal information dict
            experience: List of work experience entries
            education: List of education entries
            skills: Skills dictionary (Europass format)
            awards: Optional awards list
            publications: Optional publications list
            projects: Optional projects list
            memberships: Optional memberships list
            job_id: Optional job ID to tailor CV
            photo_url: Optional photo URL
            db: Database session
            
        Returns:
            Generated CV data with AI enhancements
        """
        logger.info(f"Generating CV for user {user_id}")
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Get user education data (from education list, not certificates)
        cert_data = []  # Certificates removed - use education list instead
        
        # Prepare user data
        user_data = {
            "full_name": personal_info.get("first_name", "") + " " + personal_info.get("surname", "") or user.full_name,
            "email": personal_info.get("email") or user.email,
            "wallet_address": user.wallet_address,
            "role": user.role.value,
            "photo_url": photo_url,
            **personal_info
        }
        
        # Generate CV with AI (certificates removed - using education list)
        cv_json = self.ai_service.generate_cv(
            user_data=user_data,
            certificates=[],  # Certificates removed - use education list instead
            experience=experience,
            education=education,
            skills=skills,
            awards=awards or [],
            publications=publications or [],
            projects=projects or [],
            memberships=memberships or [],
            job_id=job_id,
            db=db
        )
        
        # Save CV
        cv = CV(
            user_id=user_id,
            json_content=cv_json,
            ai_score=cv_json.get("ai_score"),
            photo_url=photo_url
        )
        
        db.add(cv)
        db.commit()
        db.refresh(cv)
        
        logger.info(f"CV generated with score: {cv.ai_score}")
        return {
            "id": cv.id,
            "user_id": cv.user_id,
            "json_content": cv.json_content,
            "ai_score": cv.ai_score,
            "photo_url": cv.photo_url,
            "created_at": cv.created_at.isoformat() if cv.created_at else None,
            "updated_at": cv.updated_at.isoformat() if cv.updated_at else None,
        }
    
    def get_cv(self, user_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """Get the latest CV for a user."""
        cv = db.query(CV).filter(CV.user_id == user_id).order_by(CV.created_at.desc()).first()
        if not cv:
            return None
        
        return {
            "id": cv.id,
            "user_id": cv.user_id,
            "json_content": cv.json_content,
            "ai_score": cv.ai_score,
            "photo_url": cv.photo_url,
            "created_at": cv.created_at.isoformat() if cv.created_at else None,
            "updated_at": cv.updated_at.isoformat() if cv.updated_at else None,
        }
    
    def export_to_pdf(self, cv_data: Dict[str, Any]) -> bytes:
        """
        Export CV to PDF format.
        TODO: Implement PDF generation using reportlab or weasyprint
        """
        # Placeholder for PDF export
        logger.info("Exporting CV to PDF")
        raise NotImplementedError("PDF export not yet implemented")
    
    def export_to_word(self, cv_data: Dict[str, Any]) -> bytes:
        """
        Export CV to Word format.
        TODO: Implement Word generation using python-docx
        """
        # Placeholder for Word export
        logger.info("Exporting CV to Word")
        raise NotImplementedError("Word export not yet implemented")

