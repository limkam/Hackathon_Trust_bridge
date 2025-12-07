from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import Job, User, JobMatch, Startup
from app.utils.logger import logger
from app.utils.helpers import calculate_match_score


class MatchingService:
    """Job matching service with weighted scoring algorithm."""
    
    def match_user_to_jobs(
        self,
        db: Session,
        user_id: int,
        limit: int = 10,
        category: str = None,
        location: str = None
    ) -> List[Dict[str, Any]]:
        """
        Match a user to relevant jobs based on weighted criteria.
        
        Scoring:
        - Skills match: 40%
        - Location match: 20%
        - Degree match: 20%
        - Experience match: 10%
        - Verified credentials: 10%
        """
        logger.info(f"Matching user {user_id} to jobs")
        
        # Get user data
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # Get user CV if exists
        from app.db.models import CV
        cv = db.query(CV).filter(CV.user_id == user_id).order_by(CV.created_at.desc()).first()
        user_skills = []
        user_experience_list = []
        user_degrees = []
        
        if cv and cv.json_content:
            skills_data = cv.json_content.get("skills", {})
            
            # Handle different skill formats
            if isinstance(skills_data, dict):
                # Europass format: { job_related_skills: [], computer_skills: [], social_skills: [] }
                job_skills = skills_data.get("job_related_skills", [])
                computer_skills = skills_data.get("computer_skills", [])
                social_skills = skills_data.get("social_skills", [])
                user_skills = job_skills + computer_skills + social_skills
            elif isinstance(skills_data, list):
                # Simple list format
                user_skills = [s.get("name", s) if isinstance(s, dict) else s for s in skills_data]
            else:
                user_skills = []
            
            # Normalize skills to strings
            user_skills = [str(s).lower().strip() for s in user_skills if s]
            
            # Extract education from CV
            education = cv.json_content.get("education", [])
            for edu in education:
                if isinstance(edu, dict):
                    degree = edu.get("degree") or edu.get("qualification")
                    if degree:
                        user_degrees.append(str(degree).lower().strip())
            
            # Extract actual work experience details (not just count)
            experience = cv.json_content.get("work_experience") or cv.json_content.get("experience", [])
            if isinstance(experience, list):
                user_experience_list = experience
            else:
                user_experience_list = []
            
            logger.info(f"User {user_id} has {len(user_skills)} skills, {len(user_experience_list)} experience entries, and degrees: {user_degrees}")
        
        # Optimized query: Use eager loading and filters at database level
        from sqlalchemy.orm import joinedload
        
        query = db.query(Job).options(joinedload(Job.startup))
        
        # Always join with Startup and filter out jobs without startups
        query = query.join(Startup).filter(Startup.id.isnot(None))
        
        if category:
            # Filter by startup sector at database level
            query = query.filter(Startup.sector.ilike(f"%{category}%"))
            
        if location:
            # Filter by location at database level
            query = query.filter(Job.location.ilike(f"%{location}%"))
        
        # Get ALL matching jobs (no limit) to ensure comprehensive matching
        # This allows matching against all 100+ jobs in the database
        jobs = query.all()
        
        logger.info(f"Found {len(jobs)} jobs to match against (after filters)")
        
        # Pre-calculate user skill set for faster matching
        user_skills_set = {s.lower() if isinstance(s, str) else str(s).lower() for s in user_skills}
        has_verified_certs = False  # Certificates removed - using education from CV
        
        matches = []
        for job in jobs:
            # Skip jobs without startup (orphaned jobs)
            if not job.startup:
                continue
            
            # Calculate realistic match scores
            skills_match = self._calculate_skills_match_fast(job.skills_required, user_skills_set)
            degree_match = self._calculate_degree_match_realistic(job, user_degrees)
            experience_match = self._calculate_experience_match_realistic(job, user_experience_list, job.min_experience)
            
            # Calculate overall score
            score = self._calculate_job_match_score_fast(
                job=job,
                user_skills_set=user_skills_set,
                has_verified_certs=has_verified_certs,
                user_experience=len(user_experience_list),
                user_location=None,
                skills_match=skills_match,
                degree_match=degree_match,
                experience_match=experience_match
            )
            
            # Lower threshold to show more jobs (10% instead of 20%)
            # This ensures users see jobs even if they don't have perfect matches
            if score > 0.1:
                matches.append({
                    "job_id": job.id,
                    "job_title": job.title,
                    "startup_id": job.startup_id,
                    "startup_name": job.startup.name if job.startup else None,
                    "startup_sector": job.startup.sector if job.startup else None,
                    "location": job.location,
                    "match_score": score,
                    "skills_match": skills_match,
                    "degree_match": degree_match,
                    "experience_match": experience_match
                })
        
        # Sort by match score descending
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Save top matches to database (batch operation)
        top_matches = matches[:limit]
        if top_matches:
            job_ids = [m["job_id"] for m in top_matches]
            existing_matches = db.query(JobMatch).filter(
                JobMatch.job_id.in_(job_ids),
                JobMatch.user_id == user_id
            ).all()
            existing_job_ids = {em.job_id for em in existing_matches}
            
            new_matches = [
                JobMatch(job_id=m["job_id"], user_id=user_id, score=m["match_score"])
                for m in top_matches if m["job_id"] not in existing_job_ids
            ]
            if new_matches:
                db.add_all(new_matches)
                db.commit()
        
        return top_matches
    
    # Removed _calculate_job_match_score - using _calculate_job_match_score_fast instead
    
    def _calculate_skills_match(self, required_skills: List[str], user_skills: List[str]) -> float:
        """Calculate skills match percentage."""
        if not required_skills:
            return 1.0
        if not user_skills:
            return 0.0
        
        # Normalize to lowercase for comparison
        required_lower = [s.lower() for s in required_skills]
        user_lower = [s.lower() if isinstance(s, str) else str(s).lower() for s in user_skills]
        
        matches = sum(1 for skill in required_lower if skill in user_lower)
        return matches / len(required_skills)
    
    def _calculate_skills_match_fast(self, required_skills: List[str], user_skills_set: set) -> float:
        """Fast skills match using pre-computed set."""
        if not required_skills:
            return 1.0  # No requirements = perfect match
        if not user_skills_set:
            return 0.3  # Give some score even without skills (entry-level consideration)
        
        required_set = {s.lower() for s in required_skills}
        matches = len(required_set.intersection(user_skills_set))
        base_score = matches / len(required_skills) if required_skills else 0.0
        
        # Boost score slightly if user has any skills (even if not exact match)
        if user_skills_set and base_score == 0:
            return 0.2  # Minimum score for having skills
        
        return base_score
    
    def _calculate_job_match_score_fast(
        self,
        job: Job,
        user_skills_set: set,
        has_verified_certs: bool,
        user_experience: int,
        user_location: str = None,
        skills_match: float = None,
        degree_match: float = None,
        experience_match: float = None
    ) -> float:
        """Fast version of match score calculation using pre-computed values."""
        if skills_match is None:
            skills_match = self._calculate_skills_match_fast(job.skills_required, user_skills_set)
        location_match = 1.0 if user_location and user_location.lower() == job.location.lower() else 0.5
        if degree_match is None:
            degree_match = 1.0 if has_verified_certs else 0.0
        if experience_match is None:
            experience_match = self._calculate_experience_match(job.min_experience, user_experience)
        
        return calculate_match_score(
            skills_match=skills_match,
            location_match=location_match,
            degree_match=degree_match,
            experience_match=experience_match,
            verified=has_verified_certs
        )
    
    def _calculate_degree_match_realistic(self, job: Job, user_degrees: List[str]) -> float:
        """Calculate realistic degree match by checking if user's degree is relevant to job sector."""
        if not user_degrees:
            return 0.0
        
        # Get job sector from startup
        job_sector = job.startup.sector.lower() if job.startup and job.startup.sector else ""
        job_title = job.title.lower()
        job_description = (job.description or "").lower()
        
        # Sector to degree mapping
        sector_keywords = {
            "technology": ["computer", "software", "it", "information technology", "engineering", "programming", "developer", "tech"],
            "healthcare": ["medicine", "medical", "health", "nursing", "pharmacy", "public health", "healthcare", "clinical"],
            "agriculture": ["agriculture", "agricultural", "farming", "agronomy", "crop", "livestock", "rural"],
            "education": ["education", "teaching", "pedagogy", "curriculum", "academic", "teacher"],
            "finance": ["finance", "financial", "accounting", "economics", "business", "banking", "commerce"],
            "engineering": ["engineering", "civil", "electrical", "mechanical", "structural"],
            "construction": ["construction", "civil engineering", "architecture", "building"],
        }
        
        # Check if user's degree matches job sector
        user_degree_text = " ".join(user_degrees).lower()
        
        # Check sector relevance
        if job_sector:
            relevant_keywords = sector_keywords.get(job_sector, [])
            for keyword in relevant_keywords:
                if keyword in user_degree_text or keyword in job_title or keyword in job_description:
                    # Check if user's degree contains relevant keywords
                    if any(keyword in degree for degree in user_degrees):
                        return 1.0  # Perfect match
                    # Partial match if user has any degree but job is in this sector
                    if user_degrees:
                        return 0.3  # Some relevance
        
        # If no sector match but user has education
        if user_degrees:
            return 0.1  # Very low match - has education but not relevant
        
        return 0.0
    
    def _calculate_experience_match(self, min_experience: int, user_experience: int) -> float:
        """Calculate experience match percentage."""
        if min_experience == 0:
            return 1.0
        if user_experience >= min_experience:
            return 1.0
        return user_experience / min_experience if min_experience > 0 else 0.0
    
    def _calculate_experience_match_realistic(self, job: Job, user_experience_list: List[dict], min_experience: int) -> float:
        """Calculate realistic experience match by checking if experience is relevant to the job."""
        if not user_experience_list:
            if min_experience == 0:
                return 0.5  # Entry level, no experience needed
            return 0.0  # No experience but job requires it
        
        job_title = (job.title or "").lower()
        job_description = (job.description or "").lower()
        job_sector = job.startup.sector.lower() if job.startup and job.startup.sector else ""
        
        # Extract keywords from job
        job_keywords = set()
        job_keywords.update(job_title.split())
        job_keywords.update(job_description.split()[:50])  # First 50 words
        if job_sector:
            job_keywords.add(job_sector)
        
        # Check each experience entry for relevance
        relevant_experience_count = 0
        total_experience_count = len(user_experience_list)
        
        for exp in user_experience_list:
            if not isinstance(exp, dict):
                continue
            
            # Extract experience details
            exp_title = (exp.get("title") or exp.get("position") or "").lower()
            exp_company = (exp.get("company") or exp.get("employer") or "").lower()
            exp_description = (exp.get("description") or "").lower()
            exp_responsibilities = exp.get("responsibilities", [])
            if isinstance(exp_responsibilities, str):
                exp_responsibilities = [exp_responsibilities]
            
            # Check for keyword overlap
            exp_text = f"{exp_title} {exp_company} {exp_description} {' '.join(exp_responsibilities)}".lower()
            exp_keywords = set(exp_text.split())
            
            # Calculate overlap
            overlap = len(job_keywords.intersection(exp_keywords))
            if overlap > 2:  # At least 3 matching keywords
                relevant_experience_count += 1
        
        # Calculate match based on relevant experience
        if min_experience == 0:
            # Entry level - any relevant experience is a bonus
            if relevant_experience_count > 0:
                return 1.0
            return 0.5  # No experience but job doesn't require it
        
        # Job requires experience
        if relevant_experience_count >= min_experience:
            return 1.0
        
        # Partial match
        if relevant_experience_count > 0:
            return min(0.8, relevant_experience_count / min_experience)
        
        # No relevant experience
        return 0.0

