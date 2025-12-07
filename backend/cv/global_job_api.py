"""
Global Job API Module
Searches global job market using external APIs (LinkedIn, Indeed, Talent.com, etc.)
"""
from typing import List, Dict, Any, Optional
from app.utils.logger import logger
import requests
import os


class GlobalJobAPI:
    """Global job search service using external APIs."""
    
    def __init__(self):
        # API keys from environment variables
        self.linkedin_api_key = os.getenv("LINKEDIN_API_KEY")
        self.indeed_api_key = os.getenv("INDEED_API_KEY")
        self.talent_api_key = os.getenv("TALENT_API_KEY")
    
    def search_global_jobs(
        self,
        query: str,
        location: Optional[str] = None,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search global job market across multiple APIs.
        
        Args:
            query: Job search query (e.g., "Software Engineer")
            location: Optional location filter
            limit: Maximum number of results
            filters: Optional filters (salary, experience, etc.)
            
        Returns:
            List of job listings from multiple sources
        """
        logger.info(f"Searching global jobs: {query}")
        
        all_jobs = []
        
        # Search LinkedIn Jobs (if API key available)
        if self.linkedin_api_key:
            linkedin_jobs = self._search_linkedin(query, location, limit // 3)
            all_jobs.extend(linkedin_jobs)
        
        # Search Indeed Jobs (if API key available)
        if self.indeed_api_key:
            indeed_jobs = self._search_indeed(query, location, limit // 3)
            all_jobs.extend(indeed_jobs)
        
        # Search Talent.com Jobs (if API key available)
        if self.talent_api_key:
            talent_jobs = self._search_talent(query, location, limit // 3)
            all_jobs.extend(talent_jobs)
        
        # If no API keys, return mock data for development
        if not all_jobs:
            logger.warning("No job API keys configured, returning mock data")
            all_jobs = self._get_mock_jobs(query, location, limit)
        
        # Remove duplicates and sort by relevance
        unique_jobs = self._deduplicate_jobs(all_jobs)
        
        return unique_jobs[:limit]
    
    def _search_linkedin(self, query: str, location: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Search LinkedIn Jobs API."""
        # TODO: Implement LinkedIn Jobs API integration
        # LinkedIn Jobs API requires OAuth and specific endpoints
        logger.info("LinkedIn Jobs API not yet implemented")
        return []
    
    def _search_indeed(self, query: str, location: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Search Indeed Jobs API."""
        # TODO: Implement Indeed Jobs API integration
        # Indeed has a Partner API that requires registration
        logger.info("Indeed Jobs API not yet implemented")
        return []
    
    def _search_talent(self, query: str, location: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Search Talent.com Jobs API."""
        # TODO: Implement Talent.com Jobs API integration
        logger.info("Talent.com Jobs API not yet implemented")
        return []
    
    def _get_mock_jobs(self, query: str, location: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Return mock job data for development/testing."""
        mock_jobs = [
            {
                "id": f"mock_{i}",
                "title": f"{query} - Position {i+1}",
                "company": f"Company {i+1}",
                "location": location or "Remote",
                "description": f"Job description for {query} position",
                "salary": "$50,000 - $80,000",
                "source": "mock",
                "url": f"https://example.com/job/{i}",
                "posted_date": "2024-01-01"
            }
            for i in range(min(limit, 10))
        ]
        return mock_jobs
    
    def _deduplicate_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate jobs based on title and company."""
        seen = set()
        unique = []
        
        for job in jobs:
            key = (job.get("title", "").lower(), job.get("company", "").lower())
            if key not in seen:
                seen.add(key)
                unique.append(job)
        
        return unique
    
    def match_cv_to_global_jobs(
        self,
        cv_data: Dict[str, Any],
        query: str,
        location: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Match CV to global job opportunities.
        
        Returns:
            List of matched jobs with relevance scores
        """
        logger.info("Matching CV to global jobs")
        
        # Search global jobs
        jobs = self.search_global_jobs(query, location, limit * 2)
        
        # Extract skills from CV
        cv_skills = []
        if "personal_skills" in cv_data:
            skills_data = cv_data["personal_skills"]
            if isinstance(skills_data, dict):
                cv_skills.extend(skills_data.get("job_related_skills", []))
                cv_skills.extend(skills_data.get("computer_skills", []))
        
        # Calculate match scores
        matched_jobs = []
        for job in jobs:
            score = self._calculate_match_score(cv_data, job, cv_skills)
            if score > 0.3:  # Only include jobs with >30% match
                job["match_score"] = score
                matched_jobs.append(job)
        
        # Sort by match score
        matched_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        return matched_jobs[:limit]
    
    def _calculate_match_score(
        self,
        cv_data: Dict[str, Any],
        job: Dict[str, Any],
        cv_skills: List[str]
    ) -> float:
        """Calculate match score between CV and job."""
        score = 0.0
        
        # Title match
        job_title = job.get("title", "").lower()
        cv_text = str(cv_data).lower()
        if any(word in cv_text for word in job_title.split()):
            score += 0.3
        
        # Skills match
        job_desc = job.get("description", "").lower()
        cv_skills_lower = [s.lower() for s in cv_skills]
        matching_skills = sum(1 for skill in cv_skills_lower if skill in job_desc)
        if cv_skills:
            score += min(0.5, (matching_skills / len(cv_skills)) * 0.5)
        
        # Experience match (basic heuristic)
        experience = cv_data.get("work_experience", [])
        if experience and len(experience) > 0:
            score += 0.2
        
        return min(1.0, score)

