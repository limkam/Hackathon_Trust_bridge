"""
ATS Optimizer Module
Optimizes CVs for Applicant Tracking Systems with keyword matching and formatting.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.services.ai_service import AIService
from app.utils.logger import logger


class ATSOptimizer:
    """ATS optimization service."""
    
    def __init__(self):
        self.ai_service = AIService()
    
    def calculate_ats_score(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate ATS compatibility score with detailed feedback.
        
        Returns:
            {
                "score": float (0-100),
                "keyword_density": float,
                "section_completeness": dict,
                "formatting_score": float,
                "recommendations": List[str]
            }
        """
        logger.info("Calculating ATS score")
        
        # Optimize CV for ATS
        optimized_cv = self.ai_service.optimize_for_ats(cv_data)
        
        ats_data = optimized_cv.get("ats_optimized", {})
        
        return {
            "score": ats_data.get("formatting_score", 0),
            "keyword_density": ats_data.get("keyword_density", 0),
            "section_completeness": ats_data.get("section_completeness", {}),
            "formatting_score": ats_data.get("formatting_score", 0),
            "recommendations": ats_data.get("recommendations", [])
        }
    
    def optimize_for_job(self, cv_data: Dict[str, Any], job_description: str, job_skills: List[str], job_title: str) -> Dict[str, Any]:
        """
        Optimize CV for a specific job posting.
        
        Returns:
            Optimized CV with job-specific keywords and formatting
        """
        logger.info(f"Optimizing CV for job: {job_title}")
        
        tailored_cv = self.ai_service.tailor_cv_to_job(
            cv_data,
            job_description,
            job_skills,
            job_title
        )
        
        # Further optimize for ATS
        optimized_cv = self.ai_service.optimize_for_ats(tailored_cv)
        
        return optimized_cv
    
    def get_suggestions(self, section: str, content: str, industry: str = None, db: Session = None) -> Dict[str, Any]:
        """
        Get real-time suggestions for improving CV content.
        FIRST analyzes job market to understand trending skills and keywords,
        THEN provides suggestions based on market analysis.
        
        Returns:
            {
                "improvements": List[Dict],
                "examples": List[str],
                "recommendations": List[str],
                "market_analysis": Dict (trending skills, keywords, etc.)
            }
        """
        logger.info(f"Getting suggestions for section: {section} with market analysis")
        
        # STEP 1: Analyze job market FIRST
        market_analysis = {}
        if db and industry:
            try:
                market_analysis = self.ai_service.analyze_job_market(db, sector=industry)
                logger.info(f"Market analysis complete: {len(market_analysis.get('trending_skills', []))} trending skills found")
            except Exception as e:
                logger.warning(f"Market analysis failed: {str(e)}, continuing without it")
        
        # STEP 2: Get AI suggestions (now informed by market analysis)
        suggestions = self.ai_service.get_realtime_suggestions(section, content, industry)
        
        # STEP 3: Enhance suggestions with market insights
        if market_analysis:
            trending_skills = [s.get("skill") for s in market_analysis.get("trending_skills", [])[:5]]
            trending_keywords = [k.get("keyword") for k in market_analysis.get("trending_keywords", [])[:5]]
            
            # Add market-based recommendations
            market_recommendations = market_analysis.get("recommendations", [])
            if market_recommendations:
                suggestions["recommendations"] = suggestions.get("recommendations", []) + market_recommendations
            
            # Add trending skills to recommendations if not already present
            if trending_skills:
                skills_rec = f"Consider highlighting these trending skills: {', '.join(trending_skills)}"
                if skills_rec not in suggestions.get("recommendations", []):
                    suggestions["recommendations"].append(skills_rec)
        
        # Add market analysis to response
        suggestions["market_analysis"] = market_analysis
        
        return suggestions

