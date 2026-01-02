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
        
        # Search RemoteOK (free public API - no key needed!)
        logger.info("Searching RemoteOK for remote opportunities...")
        remoteok_jobs = self._search_remoteok(query, location, limit)
        all_jobs.extend(remoteok_jobs)
        
        # Search Freelancer.com (for freelance/gig work)
        logger.info("Searching Freelancer.com for freelance projects...")
        freelancer_jobs = self._search_freelancer(query, location, limit // 2)
        all_jobs.extend(freelancer_jobs)
        
        # If no jobs found, return mock data for development
        if not all_jobs:
            logger.warning("No jobs found from APIs, returning mock data")
            all_jobs = self._get_mock_jobs(query, location, limit)
        
        # Remove duplicates and sort by relevance
        unique_jobs = self._deduplicate_jobs(all_jobs)
        
        logger.info(f"Total jobs found: {len(unique_jobs)}")
        return unique_jobs[:limit]
    
    
    def _search_remoteok(self, query: str, location: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """
        Search RemoteOK API for remote jobs.
        RemoteOK has a free public API: https://remoteok.com/api
        """
        try:
            logger.info(f"Searching RemoteOK for: {query}")
            
            # RemoteOK API endpoint
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
            query_words = query_lower.split()  # Split query into words
            
            for job in jobs_data[:limit * 3]:  # Get more for filtering
                # Filter by query - more flexible matching
                title = job.get("position", "").lower()
                tags = [tag.lower() for tag in job.get("tags", [])]
                company = job.get("company", "").lower()
                description = job.get("description", "").lower()
                
                # Match if ANY query word is in title, tags, or description
                match_score = 0
                for word in query_words:
                    if len(word) < 3:  # Skip short words
                        continue
                    if word in title:
                        match_score += 3  # Title match is most important
                    if any(word in tag for tag in tags):
                        match_score += 2  # Tag match is important
                    if word in description[:500]:  # Check first 500 chars of description
                        match_score += 1
                
                # Include job if it has any matches
                if match_score > 0:
                    formatted_job = {
                        "id": job.get("id", ""),
                        "title": job.get("position", ""),
                        "company": job.get("company", ""),
                        "location": "Remote",  # RemoteOK is all remote
                        "description": job.get("description", "")[:500] + "..." if len(job.get("description", "")) > 500 else job.get("description", ""),
                        "salary": job.get("salary_min", "") or "Competitive",
                        "source": "RemoteOK",
                        "url": job.get("url", ""),
                        "posted_date": job.get("date", ""),
                        "tags": job.get("tags", []),
                        "logo": job.get("logo", ""),
                        "match_score": match_score  # For sorting
                    }
                    jobs.append(formatted_job)
            
            # Sort by match score
            jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            
            logger.info(f"Found {len(jobs)} jobs from RemoteOK")
            return jobs[:limit]
            
        except Exception as e:
            logger.error(f"RemoteOK API error: {str(e)}")
            return []
    
    
    def _search_freelancer(
        self,
        query: str,
        location: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search Freelancer.com for freelance projects.
        Uses Freelancer's public API endpoint.
        """
        try:
            logger.info(f"Searching Freelancer.com for: {query}")
            
            # Freelancer API endpoint (public projects)
            url = "https://www.freelancer.com/api/projects/0.1/projects/active/"
            
            headers = {
                "User-Agent": "TrustBridge-JobMatcher/1.0"
            }
            
            params = {
                "query": query,
                "limit": limit,
                "compact": True  # Get compact response
            }
            
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Freelancer API error: {response.status_code}")
                return []
            
            # Parse JSON response
            try:
                data = response.json()
            except Exception as json_error:
                logger.error(f"Failed to parse Freelancer JSON: {json_error}")
                return []
            
            # Extract projects from response
            if not data.get("result") or not data["result"].get("projects"):
                logger.info("No projects found from Freelancer")
                return []
            
            projects = data["result"]["projects"]
            
            # Format projects
            jobs = []
            for project in projects[:limit]:
                try:
                    # Format budget safely
                    budget = project.get("budget", {})
                    currency_data = project.get("currency", {})
                    currency = currency_data.get("code", "USD") if isinstance(currency_data, dict) else "USD"
                    
                    min_budget = budget.get("minimum", 0) if isinstance(budget, dict) else 0
                    max_budget = budget.get("maximum", "?") if isinstance(budget, dict) else "?"
                    budget_str = f"{currency} {min_budget} - {max_budget}"
                    
                    # Extract tags from jobs
                    tags = []
                    if project.get("jobs") and isinstance(project["jobs"], list):
                        tags = [job.get("name", "") for job in project["jobs"] if isinstance(job, dict)]
                    
                    # Format posted date
                    posted_timestamp = project.get("submitdate", 0)
                    from datetime import datetime
                    posted_date = datetime.fromtimestamp(posted_timestamp).strftime("%Y-%m-%d") if posted_timestamp else ""
                    
                    formatted_job = {
                        "id": str(project.get("id", "")),
                        "title": project.get("title", "Untitled Project"),
                        "company": "Freelancer Client",  # Freelancer hides client names
                        "location": "Remote (Freelance)",
                        "description": project.get("preview_description", project.get("description", ""))[:500],
                        "salary": budget_str,
                        "source": "Freelancer.com",
                        "url": f"https://www.freelancer.com/projects/{project.get('seo_url', '')}",
                        "posted_date": posted_date,
                        "tags": tags,
                        "type": project.get("type", {}).get("name", "Fixed Price") if isinstance(project.get("type"), dict) else "Fixed Price"
                    }
                    jobs.append(formatted_job)
                except Exception as project_error:
                    logger.warning(f"Error parsing Freelancer project: {project_error}")
                    continue
            
            logger.info(f"Found {len(jobs)} projects from Freelancer.com")
            return jobs
            
        except Exception as e:
            logger.error(f"Freelancer.com API error: {str(e)}")
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

