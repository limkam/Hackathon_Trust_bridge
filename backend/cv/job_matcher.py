"""
Job Matcher Module
Matches users to relevant job opportunities using AI-powered ranking.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.matching_service import MatchingService
from app.utils.logger import logger


class JobMatcher:
    """Job matching service with AI-powered ranking."""
    
    def __init__(self):
        self.matching_service = MatchingService()
    
    def match_user_to_jobs(
        self,
        user_id: int,
        limit: int = 10,
        category: Optional[str] = None,
        location: Optional[str] = None,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Match a user to relevant jobs.
        
        Returns:
            List of matched jobs with scores and details
        """
        logger.info(f"Matching user {user_id} to jobs")
        
        matches = self.matching_service.match_user_to_jobs(
            db=db,
            user_id=user_id,
            limit=limit,
            category=category,
            location=location
        )
        
        return matches
    
    def improve_ranking_for_ats(
        self,
        cv_data: Dict[str, Any],
        job_description: str,
        job_skills: List[str]
    ) -> Dict[str, Any]:
        """
        Improve CV ranking for ATS systems by optimizing keywords and structure.
        
        Returns:
            Optimized CV data with ATS improvements
        """
        logger.info("Improving CV ranking for ATS")
        
        from app.services.ai_service import AIService
        ai_service = AIService()
        
        # Extract keywords from job
        job_keywords = ai_service._extract_keywords_from_job(job_description, job_skills)
        
        # Enhance CV with job keywords
        optimized_cv = ai_service.optimize_for_ats(cv_data)
        
        # Add ranking improvements
        optimized_cv["ats_ranking_improvements"] = {
            "keywords_added": job_keywords[:10],
            "keyword_density": ai_service._calculate_keyword_density(optimized_cv),
            "recommendations": ai_service._generate_ats_recommendations(optimized_cv)
        }
        
        return optimized_cv

