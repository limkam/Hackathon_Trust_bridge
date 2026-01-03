"""
Job Aggregator Service
Fetches jobs from RemoteOK and Freelancer.com
"""
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.utils.logger import logger
from app.core.config import settings


class JobAggregator:
    """Aggregates jobs from RemoteOK and Freelancer.com."""

    def __init__(self):
        # No API keys needed for RemoteOK (free public API)
        # Freelancer.com will need OAuth in the future
        pass

    def search_jobs(
        self,
        keywords: List[str],
        job_titles: Optional[List[str]] = None,
        location: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search jobs from RemoteOK and Freelancer.com.
        
        Args:
            keywords: List of keywords from CV
            job_titles: Optional list of suggested job titles
            location: Optional location filter (ignored for remote jobs)
            limit: Maximum number of results
            
        Returns:
            List of normalized job objects
        """
        logger.info(f"Searching jobs for keywords: {keywords}")
        
        all_jobs = []
        
        # Combine keywords and job titles for search
        search_terms = keywords.copy()
        if job_titles:
            search_terms.extend(job_titles)
        
        # Remove duplicates and create search query
        search_query = " ".join(list(set(search_terms))[:5])  # Limit to 5 terms
        
        # Search RemoteOK
        try:
            logger.info("Searching RemoteOK...")
            remoteok_jobs = self._search_remoteok(search_query, limit)
            all_jobs.extend(remoteok_jobs)
            logger.info(f"Found {len(remoteok_jobs)} jobs from RemoteOK")
        except Exception as e:
            logger.warning(f"RemoteOK search failed: {str(e)}")
        
        # Search Freelancer.com (placeholder for now)
        try:
            logger.info("Searching Freelancer.com...")
            freelancer_jobs = self._search_freelancer(search_query, limit // 2)
            all_jobs.extend(freelancer_jobs)
            logger.info(f"Found {len(freelancer_jobs)} jobs from Freelancer.com")
        except Exception as e:
            logger.warning(f"Freelancer.com search failed: {str(e)}")
        
        # Deduplicate and normalize
        normalized_jobs = self._deduplicate_jobs(all_jobs)
        
        # Rank by relevance
        ranked_jobs = self._rank_by_relevance(normalized_jobs, keywords, job_titles)
        
        logger.info(f"Total unique jobs found: {len(ranked_jobs)}")
        return ranked_jobs[:limit]

    def _search_remoteok(
        self,
        query: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search RemoteOK API for remote jobs.
        Free public API - no authentication required.
        """
        try:
            url = "https://remoteok.com/api"
            
            headers = {
                "User-Agent": "TrustBridge-JobMatcher/1.0"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"RemoteOK API error: {response.status_code}")
                return []
            
            data = response.json()
            
            # First item is metadata, skip it
            if data and isinstance(data, list) and len(data) > 1:
                jobs_data = data[1:]
            else:
                return []
            
            # Filter and format jobs
            jobs = []
            query_lower = query.lower()
            query_words = query_lower.split()
            
            for job in jobs_data[:limit * 3]:
                # Filter by query - flexible matching
                title = job.get("position", "").lower()
                tags = [tag.lower() for tag in job.get("tags", [])]
                description = job.get("description", "").lower()
                
                # Match scoring
                match_score = 0
                for word in query_words:
                    if len(word) < 3:
                        continue
                    if word in title:
                        match_score += 3
                    if any(word in tag for tag in tags):
                        match_score += 2
                    if word in description[:500]:
                        match_score += 1
                
                if match_score > 0:
                    formatted_job = {
                        "title": job.get("position", ""),
                        "company": job.get("company", "Unknown"),
                        "location": "Remote",
                        "description": job.get("description", "")[:500] + "..." if len(job.get("description", "")) > 500 else job.get("description", ""),
                        "applyUrl": job.get("url", ""),
                        "source": "RemoteOK",
                        "posted_date": job.get("date", ""),
                        "tags": job.get("tags", []),
                        "logo": job.get("logo", ""),
                        "match_score": match_score
                    }
                    jobs.append(formatted_job)
            
            # Sort by match score
            jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            
            return jobs[:limit]
            
        except Exception as e:
            logger.error(f"RemoteOK API error: {str(e)}")
            return []

    def _search_freelancer(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search Freelancer.com for freelance projects.
        Placeholder - requires OAuth for full implementation.
        """
        try:
            logger.info("Freelancer.com requires OAuth - placeholder for now")
            # TODO: Implement Freelancer API OAuth flow
            # For now, return empty array
            return []
            
        except Exception as e:
            logger.error(f"Freelancer.com API error: {str(e)}")
            return []

    def _deduplicate_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate jobs based on title and company."""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Create a key from title and company
            key = (
                job.get("title", "").lower().strip(),
                job.get("company", "").lower().strip()
            )
            
            if key not in seen and job.get("applyUrl"):
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs

    def _rank_by_relevance(
        self,
        jobs: List[Dict[str, Any]],
        keywords: List[str],
        job_titles: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Rank jobs by relevance to CV keywords and job titles."""
        keywords_lower = [k.lower() for k in keywords]
        titles_lower = [t.lower() for t in job_titles] if job_titles else []
        
        def calculate_score(job: Dict[str, Any]) -> float:
            score = job.get("match_score", 0.0)  # Start with existing match score
            title = job.get("title", "").lower()
            description = job.get("description", "").lower()
            company = job.get("company", "").lower()
            
            # Check title matches
            for keyword in keywords_lower:
                if keyword in title:
                    score += 3.0
                if keyword in description:
                    score += 1.0
                if keyword in company:
                    score += 0.5
            
            # Check job title matches
            for job_title in titles_lower:
                if job_title in title:
                    score += 5.0
                if any(word in title for word in job_title.split()):
                    score += 2.0
            
            # Boost remote jobs (already all remote from RemoteOK)
            if "remote" in title.lower() or "remote" in description.lower():
                score += 1.0
            
            return score
        
        # Calculate scores and sort
        scored_jobs = [(job, calculate_score(job)) for job in jobs]
        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        
        return [job for job, score in scored_jobs]
