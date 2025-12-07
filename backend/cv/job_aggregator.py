"""
Job Aggregator Service
Fetches jobs from multiple free APIs: Adzuna, Jooble, SerpAPI, and RSS feeds
"""
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import feedparser
import sys
from pathlib import Path

# Add backend/app to path for imports
backend_dir = Path(__file__).parent.parent
app_dir = backend_dir / "app"
sys.path.insert(0, str(app_dir))

from utils.logger import logger
from core.config import settings
import re


class JobAggregator:
    """Aggregates jobs from multiple free sources."""

    def __init__(self):
        # API keys from settings (automatically loads from .env)
        self.adzuna_app_id = settings.ADZUNA_APP_ID
        self.adzuna_app_key = settings.ADZUNA_APP_KEY
        self.jooble_api_key = settings.JOOBLE_API_KEY
        self.serpapi_key = settings.SERPAPI_KEY
        
        # Adzuna base URL (free tier available)
        self.adzuna_base_url = "https://api.adzuna.com/v1/api/jobs"
        
        # Jooble base URL
        self.jooble_base_url = "https://jooble.org/api"
        
        # SerpAPI base URL
        self.serpapi_base_url = "https://serpapi.com/search"

    def search_jobs(
        self,
        keywords: List[str],
        job_titles: Optional[List[str]] = None,
        location: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search jobs from all sources and return normalized results.
        
        Args:
            keywords: List of keywords from CV
            job_titles: Optional list of suggested job titles
            location: Optional location filter
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
        
        # Search APIs with timeout protection - use try/except for each to prevent hanging
        try:
            adzuna_jobs = self._search_adzuna(search_query, location, limit // 4)
            all_jobs.extend(adzuna_jobs)
        except Exception as e:
            logger.warning(f"Adzuna search failed: {str(e)}")
        
        try:
            jooble_jobs = self._search_jooble(search_query, location, limit // 4)
            all_jobs.extend(jooble_jobs)
        except Exception as e:
            logger.warning(f"Jooble search failed: {str(e)}")
        
        try:
            serpapi_jobs = self._search_serpapi(search_query, location, limit // 4)
            all_jobs.extend(serpapi_jobs)
        except Exception as e:
            logger.warning(f"SerpAPI search failed: {str(e)}")
        
        try:
            rss_jobs = self._search_rss_feeds(search_query, limit // 4)
            all_jobs.extend(rss_jobs)
        except Exception as e:
            logger.warning(f"RSS feed search failed: {str(e)}")
        
        # Deduplicate and normalize
        normalized_jobs = self._deduplicate_jobs(all_jobs)
        
        # Rank by relevance
        ranked_jobs = self._rank_by_relevance(normalized_jobs, keywords, job_titles)
        
        return ranked_jobs[:limit]

    def _search_adzuna(
        self,
        query: str,
        location: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search Adzuna API (free tier available)."""
        if not self.adzuna_app_id or not self.adzuna_app_key:
            logger.warning("Adzuna API keys not configured")
            return []
        
        try:
            params = {
                "app_id": self.adzuna_app_id,
                "app_key": self.adzuna_app_key,
                "results_per_page": min(limit, 50),
                "what": query,
                "content-type": "application/json"
            }
            
            if location:
                params["where"] = location
            
            # Try first country only to avoid hanging (was trying multiple countries)
            country = "us"  # Default to US
            params["where0"] = country
            response = requests.get(
                f"{self.adzuna_base_url}/{country}/search/1",
                params=params,
                timeout=5  # Reduced timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = []
                for result in data.get("results", [])[:limit]:
                    jobs.append({
                        "title": result.get("title", ""),
                        "company": result.get("company", {}).get("display_name", "Unknown"),
                        "location": result.get("location", {}).get("display_name", location or "Remote"),
                        "description": result.get("description", ""),
                        "applyUrl": result.get("redirect_url", ""),
                        "source": "Adzuna",
                        "posted_date": result.get("created", "")
                    })
                return jobs
        except Exception as e:
            logger.error(f"Adzuna API error: {str(e)}")
        
        return []

    def _search_jooble(
        self,
        query: str,
        location: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search Jooble API."""
        if not self.jooble_api_key:
            logger.warning("Jooble API key not configured")
            return []
        
        try:
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "keywords": query,
                "location": location or "",
                "radius": "25",
                "page": 1,
                "searchMode": 1
            }
            
            response = requests.post(
                f"{self.jooble_base_url}/{self.jooble_api_key}",
                json=payload,
                headers=headers,
                timeout=5  # Reduced timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = []
                for result in data.get("jobs", [])[:limit]:
                    jobs.append({
                        "title": result.get("title", ""),
                        "company": result.get("company", "Unknown"),
                        "location": result.get("location", location or "Remote"),
                        "description": result.get("snippet", ""),
                        "applyUrl": result.get("link", ""),
                        "source": "Jooble",
                        "posted_date": result.get("updated", "")
                    })
                return jobs
        except Exception as e:
            logger.error(f"Jooble API error: {str(e)}")
        
        return []

    def _search_serpapi(
        self,
        query: str,
        location: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search SerpAPI (Google Jobs)."""
        if not self.serpapi_key:
            logger.warning("SerpAPI key not configured")
            return []
        
        try:
            params = {
                "api_key": self.serpapi_key,
                "engine": "google_jobs",
                "q": query,
                "location": location or "United States",
                "num": min(limit, 100)
            }
            
            response = requests.get(
                self.serpapi_base_url,
                params=params,
                timeout=5  # Reduced timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = []
                for result in data.get("jobs_results", [])[:limit]:
                    jobs.append({
                        "title": result.get("title", ""),
                        "company": result.get("company_name", "Unknown"),
                        "location": result.get("location", location or "Remote"),
                        "description": result.get("description", ""),
                        "applyUrl": result.get("apply_options", [{}])[0].get("link", "") if result.get("apply_options") else "",
                        "source": "Google Jobs",
                        "posted_date": result.get("detected_extensions", {}).get("posted_at", "")
                    })
                return jobs
        except Exception as e:
            logger.error(f"SerpAPI error: {str(e)}")
        
        return []

    def _search_rss_feeds(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search remote/freelance job RSS feeds."""
        jobs = []
        
        # Free RSS feed sources
        rss_feeds = [
            "https://www.remoteok.io/remote-jobs.rss",
            "https://weworkremotely.com/categories/remote-programming-jobs.rss",
            "https://www.flexjobs.com/rss/jobs.rss",
        ]
        
        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:limit // len(rss_feeds)]:
                    # Check if entry matches keywords
                    title_lower = entry.get("title", "").lower()
                    description_lower = entry.get("summary", "").lower()
                    query_lower = query.lower()
                    
                    if any(keyword.lower() in title_lower or keyword.lower() in description_lower 
                           for keyword in query.split()):
                        jobs.append({
                            "title": entry.get("title", ""),
                            "company": self._extract_company_from_rss(entry),
                            "location": "Remote",
                            "description": entry.get("summary", "")[:500],  # Limit description
                            "applyUrl": entry.get("link", ""),
                            "source": "RSS Feed",
                            "posted_date": entry.get("published", "")
                        })
            except Exception as e:
                logger.error(f"RSS feed error ({feed_url}): {str(e)}")
        
        return jobs

    def _extract_company_from_rss(self, entry: Dict) -> str:
        """Extract company name from RSS entry."""
        title = entry.get("title", "")
        # Try to extract company from title (format: "Job Title - Company Name")
        if " - " in title:
            return title.split(" - ")[-1]
        return "Unknown"

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
            score = 0.0
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
            
            # Boost remote jobs
            if "remote" in title.lower() or "remote" in description.lower():
                score += 1.0
            
            return score
        
        # Calculate scores and sort
        scored_jobs = [(job, calculate_score(job)) for job in jobs]
        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        
        return [job for job, score in scored_jobs]

