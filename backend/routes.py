"""
Main API Routes
Exposes endpoints for CV Builder and Investment Platform.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
from pathlib import Path

import sys
from pathlib import Path

# Add backend/app to path for imports
backend_dir = Path(__file__).parent
app_dir = backend_dir / "app"
sys.path.insert(0, str(app_dir))

from db.session import get_db
from db.models import User, Startup, Investment, Job
from core.config import settings
from utils.logger import logger
from sqlalchemy import func, or_

# Import new modules
import sys
from pathlib import Path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from cv.cv_generator import CVGenerator
from cv.ats_optimizer import ATSOptimizer
from cv.job_matcher import JobMatcher
from cv.global_job_api import GlobalJobAPI
from cv.job_aggregator import JobAggregator
from investments.startup_verification import StartupVerification
from investments.usdc_transactions import USDCTransactions
from investments.investor_portfolio import InvestorPortfolio
from app.services.advanced_cv_service import AdvancedCVService
from app.blockchain.startup_client import StartupClient

router = APIRouter()

# Initialize services
cv_generator = CVGenerator()
ats_optimizer = ATSOptimizer()
job_matcher = JobMatcher()
global_job_api = GlobalJobAPI()
job_aggregator = JobAggregator()
startup_verification = StartupVerification()
usdc_transactions = USDCTransactions()
investor_portfolio = InvestorPortfolio()
advanced_cv_service = AdvancedCVService()


# ==================== CV BUILDER ENDPOINTS ====================

class CVGenerateRequest(BaseModel):
    user_id: int
    personal_info: Dict[str, Any]
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    skills: Dict[str, Any]
    awards: Optional[List[Dict[str, Any]]] = None
    publications: Optional[List[Dict[str, Any]]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    memberships: Optional[List[Dict[str, Any]]] = None
    job_id: Optional[int] = None


@router.post("/api/cv/generate")
async def generate_cv_endpoint(
    user_id: int = Form(...),
    personal_info: str = Form("{}"),
    experience: str = Form("[]"),
    education: str = Form("[]"),
    skills: str = Form("{}"),
    awards: str = Form("[]"),
    publications: str = Form("[]"),
    projects: str = Form("[]"),
    memberships: str = Form("[]"),
    job_id: Optional[int] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Generate a professional CV with AI enhancements."""
    try:
        # Parse JSON strings
        personal_info_dict = json.loads(personal_info) if personal_info else {}
        experience_list = json.loads(experience) if experience else []
        education_list = json.loads(education) if education else []
        skills_dict = json.loads(skills) if skills else {}
        awards_list = json.loads(awards) if awards else []
        publications_list = json.loads(publications) if publications else []
        projects_list = json.loads(projects) if projects else []
        memberships_list = json.loads(memberships) if memberships else []
        
        # Handle photo upload
        photo_url = None
        if photo:
            # Save photo
            import shutil
            import uuid
            upload_dir = Path(settings.UPLOAD_DIR)
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_ext = Path(photo.filename).suffix
            unique_filename = f"{user_id}_{uuid.uuid4().hex}{file_ext}"
            file_path = upload_dir / unique_filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(photo.file, buffer)
            photo_url = f"/static/uploads/{unique_filename}"
        
        # Generate CV
        result = cv_generator.generate_cv(
            user_id=user_id,
            personal_info=personal_info_dict,
            experience=experience_list,
            education=education_list,
            skills=skills_dict,
            awards=awards_list,
            publications=publications_list,
            projects=projects_list,
            memberships=memberships_list,
            job_id=job_id,
            photo_url=photo_url,
            db=db
        )
        
        return result
    except Exception as e:
        logger.error(f"Error generating CV: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate CV: {str(e)}"
        )


@router.get("/api/cv/{user_id}")
async def get_cv_endpoint(user_id: int, db: Session = Depends(get_db)):
    """Get the latest CV for a user."""
    cv = cv_generator.get_cv(user_id, db)
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CV not found for user {user_id}"
        )
    return cv


@router.post("/api/cv/upload-photo")
async def upload_photo_endpoint(
    photo: UploadFile = File(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Upload CV photo."""
    try:
        import shutil
        import uuid
        from pathlib import Path
        
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_ext = Path(photo.filename).suffix
        unique_filename = f"{user_id}_{uuid.uuid4().hex}{file_ext}"
        file_path = upload_dir / unique_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        
        photo_url = f"/static/uploads/{unique_filename}"
        
        return {
            "success": True,
            "photo_url": photo_url
        }
    except Exception as e:
        logger.error(f"Error uploading photo: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload photo: {str(e)}"
        )


@router.post("/api/cv/save")
async def save_cv_endpoint(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Save CV to database (accepts JSON)."""
    try:
        user_id = request.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id is required"
            )
        
        # Prepare CV data
        personal_info = request.get("personal_info", {})
        experience = request.get("experience", [])
        education = request.get("education", [])
        skills = request.get("skills", {})
        awards = request.get("awards", [])
        publications = request.get("publications", [])
        projects = request.get("projects", [])
        memberships = request.get("memberships", [])
        photo_url = request.get("photo_url")
        
        # Generate and save CV
        result = cv_generator.generate_cv(
            user_id=user_id,
            personal_info=personal_info,
            experience=experience,
            education=education,
            skills=skills,
            awards=awards,
            publications=publications,
            projects=projects,
            memberships=memberships,
            job_id=None,
            photo_url=photo_url,
            db=db
        )
        
        return result
    except Exception as e:
        logger.error(f"Error saving CV: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save CV: {str(e)}"
        )


@router.post("/api/cv/suggestions")
async def get_cv_suggestions(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Get AI-powered suggestions for CV content with market analysis."""
    try:
        section = request.get("section", "")
        content = request.get("content", "")
        industry = request.get("industry")
        # Pass db for market analysis
        suggestions = ats_optimizer.get_suggestions(section, content, industry, db)
        return suggestions
    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )


@router.post("/api/cv/ats-score")
async def calculate_ats_score_endpoint(cv_data: Dict[str, Any]):
    """Calculate ATS compatibility score."""
    try:
        score_data = ats_optimizer.calculate_ats_score(cv_data)
        return score_data
    except Exception as e:
        logger.error(f"Error calculating ATS score: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate ATS score: {str(e)}"
        )


# ==================== ADVANCED CV FEATURES ====================

@router.post("/api/cv/generate-from-questions")
async def generate_cv_from_questions(request: Dict[str, Any]):
    """Generate CV from guided questionnaire answers."""
    try:
        result = advanced_cv_service.generate_cv_from_questions(request)
        return result
    except Exception as e:
        logger.error(f"Error generating CV from questions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate CV: {str(e)}"
        )


@router.post("/api/cv/match-job")
async def match_job_compatibility(request: Dict[str, Any]):
    """Match CV to job description and compute compatibility score."""
    try:
        cv_data = request.get("cv_data", {})
        job_description = request.get("job_description", "")
        
        if not job_description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description is required"
            )
        
        result = advanced_cv_service.match_job_compatibility(cv_data, job_description)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to match job: {str(e)}"
        )


@router.post("/api/cv/optimize-for-job")
async def optimize_cv_for_job(request: Dict[str, Any]):
    """Generate job-optimized version of CV."""
    try:
        cv_data = request.get("cv_data", {})
        job_description = request.get("job_description", "")
        
        if not job_description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description is required"
            )
        
        result = advanced_cv_service.generate_job_optimized_cv(cv_data, job_description)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing CV: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize CV: {str(e)}"
        )


@router.post("/api/cv/generate-cover-letter")
async def generate_cover_letter(request: Dict[str, Any]):
    """Generate personalized cover letter."""
    try:
        cv_data = request.get("cv_data", {})
        job_description = request.get("job_description", "")
        company_name = request.get("company_name", "")
        
        if not job_description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description is required"
            )
        
        result = advanced_cv_service.generate_cover_letter(cv_data, job_description, company_name)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating cover letter: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cover letter: {str(e)}"
        )


@router.post("/api/cv/extract-skills")
async def extract_skills_from_cv(request: Dict[str, Any]):
    """Extract and categorize skills from CV."""
    try:
        cv_data = request.get("cv_data", {})
        result = advanced_cv_service.extract_skills_from_cv(cv_data)
        return result
    except Exception as e:
        logger.error(f"Error extracting skills: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract skills: {str(e)}"
        )


@router.post("/api/cv/generate-interview-questions")
async def generate_interview_questions(request: Dict[str, Any]):
    """Generate interview questions based on CV and job description."""
    try:
        cv_data = request.get("cv_data", {})
        job_description = request.get("job_description", "")
        
        if not job_description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description is required"
            )
        
        result = advanced_cv_service.generate_interview_questions(cv_data, job_description)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate questions: {str(e)}"
        )


@router.post("/api/cv/optimize-ats")
async def optimize_ats_endpoint(request: Dict[str, Any]):
    """Comprehensive ATS optimization analysis."""
    try:
        cv_data = request.get("cv_data", {})
        result = advanced_cv_service.optimize_ats(cv_data)
        return result
    except Exception as e:
        logger.error(f"Error optimizing ATS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize ATS: {str(e)}"
        )


@router.post("/api/cv/career-recommendations")
async def get_career_recommendations(request: Dict[str, Any]):
    """Get career path recommendations based on CV."""
    try:
        cv_data = request.get("cv_data", {})
        result = advanced_cv_service.generate_career_recommendations(cv_data)
        return result
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.post("/api/cv/field-suggestions")
async def get_field_suggestions(request: Dict[str, Any]):
    """Get 10+ AI suggestions for a specific CV field."""
    try:
        field = request.get("field", "")
        current_value = request.get("current_value", "")
        context = request.get("context", {})
        
        if not field:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Field is required"
            )
        
        result = advanced_cv_service.get_field_suggestions(field, current_value, context)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting field suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )


@router.post("/api/cv/upload-linkedin-pdf")
async def upload_linkedin_pdf(
    pdf_file: UploadFile = File(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Upload LinkedIn CV PDF and automatically extract information using AI.
    Returns structured CV data ready for job matching.
    """
    try:
        # Validate file type
        if not pdf_file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        # Validate file size (10MB max)
        content = await pdf_file.read()
        await pdf_file.seek(0)  # Reset file pointer
        
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum of 10MB"
            )
        
        # Import PDF parser service
        from app.services.pdf_parser_service import PDFParserService
        pdf_parser = PDFParserService()
        
        # Extract text from PDF
        logger.info(f"Extracting text from PDF for user {user_id}")
        pdf_text = await pdf_parser.extract_text_from_pdf(pdf_file)
        
        if not pdf_text or len(pdf_text) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract sufficient text from PDF. Please ensure the PDF is not scanned or encrypted."
            )
        
        # Parse CV data using Mistral AI
        logger.info(f"Parsing CV data with AI for user {user_id}")
        cv_data = await pdf_parser.parse_linkedin_cv(pdf_text)
        
        # Validate and clean data
        cv_data = pdf_parser.validate_cv_data(cv_data)
        
        # Save CV to database
        logger.info(f"Saving parsed CV to database for user {user_id}")
        result = cv_generator.generate_cv(
            user_id=user_id,
            personal_info=cv_data.get("personal_info", {}),
            experience=cv_data.get("experience", []),
            education=cv_data.get("education", []),
            skills=cv_data.get("skills", {}),
            awards=cv_data.get("awards", []),
            publications=cv_data.get("publications", []),
            projects=cv_data.get("projects", []),
            memberships=[],
            job_id=None,
            photo_url=None,
            db=db
        )
        
        # Get job matches automatically
        logger.info(f"Finding job matches for user {user_id}")
        job_matches = []
        try:
            # Extract keywords from CV
            keywords = []
            if cv_data.get("skills", {}).get("technical"):
                keywords.extend(cv_data["skills"]["technical"][:5])
            if cv_data.get("experience"):
                for exp in cv_data["experience"][:2]:
                    if exp.get("job_title"):
                        keywords.append(exp["job_title"])
            
            # Search for matching jobs
            if keywords:
                job_search_result = await search_jobs_from_cv(
                    JobSearchRequest(
                        keywords=keywords[:5],
                        job_titles=[exp.get("job_title") for exp in cv_data.get("experience", [])[:3] if exp.get("job_title")],
                        location=cv_data.get("personal_info", {}).get("address"),
                        limit=10
                    ),
                    db=db
                )
                job_matches = job_search_result.get("jobs", [])
        except Exception as e:
            logger.warning(f"Could not fetch job matches: {e}")
        
        return {
            "success": True,
            "message": "CV uploaded and parsed successfully",
            "cv_data": cv_data,
            "cv_id": result.get("id"),
            "job_matches": job_matches,
            "match_count": len(job_matches)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading LinkedIn PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PDF: {str(e)}"
        )


# ==================== GLOBAL JOB MATCHING ENDPOINTS ====================

@router.get("/api/jobs/search-global")
async def search_global_jobs(
    query: str,
    location: Optional[str] = None,
    limit: int = 20
):
    """Search global job market across multiple APIs."""
    try:
        jobs = global_job_api.search_global_jobs(query, location, limit)
        return {"jobs": jobs, "count": len(jobs)}
    except Exception as e:
        logger.error(f"Error searching global jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search jobs: {str(e)}"
        )


@router.post("/api/jobs/match")
async def match_jobs_endpoint(
    user_id: int,
    limit: int = 10,
    category: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Match user to relevant job opportunities."""
    try:
        matches = job_matcher.match_user_to_jobs(
            user_id=user_id,
            limit=limit,
            category=category,
            location=location,
            db=db
        )
        return {"matches": matches, "count": len(matches)}
    except Exception as e:
        logger.error(f"Error matching jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to match jobs: {str(e)}"
        )


@router.post("/api/jobs/match-global")
async def match_global_jobs(
    user_id: int,
    query: str,
    location: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Match user CV to global job opportunities."""
    try:
        # Get user's CV
        cv = cv_generator.get_cv(user_id, db)
        if not cv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CV not found. Please create a CV first."
            )
        
        # Match to global jobs
        matched_jobs = global_job_api.match_cv_to_global_jobs(
            cv_data=cv["json_content"],
            query=query,
            location=location,
            limit=limit
        )
        
        return {"matches": matched_jobs, "count": len(matched_jobs)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching global jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to match global jobs: {str(e)}"
        )


class JobSearchRequest(BaseModel):
    """Request model for job search based on CV keywords."""
    keywords: List[str]
    job_titles: Optional[List[str]] = None
    location: Optional[str] = None
    limit: int = 50


@router.post("/api/cv/jobs")
async def search_jobs_from_cv(
    request: JobSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search jobs based on CV keywords and job titles.
    PRIORITIZES database jobs for fast, reliable results.
    Optionally includes external APIs if available (non-blocking).
    """
    try:
        logger.info(f"Searching jobs for keywords: {request.keywords}")
        
        all_jobs = []
        sources = []
        
        # PRIORITY 1: Search database FIRST for immediate results
        try:
            logger.info("Searching database jobs...")
            # Build database query
            query = db.query(Job).join(Startup, Job.startup_id == Startup.id, isouter=True)
            
            # Filter by keywords in title or description
            if request.keywords:
                keyword_filters = []
                for keyword in request.keywords[:5]:  # Limit to 5 keywords
                    keyword_filter = (
                        Job.title.ilike(f"%{keyword}%") |
                        Job.description.ilike(f"%{keyword}%") |
                        func.array_to_string(Job.skills_required, ', ').ilike(f"%{keyword}%")
                    )
                    keyword_filters.append(keyword_filter)
                if keyword_filters:
                    query = query.filter(or_(*keyword_filters))
            
            # Filter by job titles if provided
            if request.job_titles:
                title_filters = []
                for title in request.job_titles[:3]:  # Limit to 3 titles
                    title_filters.append(Job.title.ilike(f"%{title}%"))
                if title_filters:
                    query = query.filter(or_(*title_filters))
            
            # Filter by location
            if request.location:
                query = query.filter(Job.location.ilike(f"%{request.location}%"))
            
            # Get jobs from database (prioritize database results)
            db_jobs = query.limit(request.limit).all()
            
            logger.info(f"Found {len(db_jobs)} jobs in database")
            
            # Convert database jobs to API format
            for job in db_jobs:
                company_name = job.company_name
                if not company_name and job.startup:
                    company_name = job.startup.name
                
                job_dict = {
                    "title": job.title,
                    "company": company_name or "Unknown",
                    "location": job.location,
                    "description": job.description,
                    "applyUrl": None,  # Database jobs - can add application endpoint later
                    "source": "Database",
                    "posted_date": job.created_at.isoformat() if job.created_at else None,
                    "skills": job.skills_required or [],
                    "min_experience": job.min_experience or 0,
                    "job_id": job.id,  # Include job ID for application tracking
                }
                all_jobs.append(job_dict)
            
            if db_jobs:
                sources.append("Database")
        except Exception as e:
            logger.error(f"Database job search failed: {str(e)}")
        
        # Ensure we return at least some results (even if no matches, return recent jobs)
        if len(all_jobs) == 0:
            logger.info("No matching jobs found, returning recent jobs from database")
            try:
                recent_jobs = db.query(Job).join(Startup, Job.startup_id == Startup.id, isouter=True).order_by(Job.created_at.desc()).limit(10).all()
                for job in recent_jobs:
                    company_name = job.company_name
                    if not company_name and job.startup:
                        company_name = job.startup.name
                    
                    job_dict = {
                        "title": job.title,
                        "company": company_name or "Unknown",
                        "location": job.location,
                        "description": job.description,
                        "applyUrl": None,
                        "source": "Database (Recent)",
                        "posted_date": job.created_at.isoformat() if job.created_at else None,
                        "skills": job.skills_required or [],
                        "min_experience": job.min_experience or 0,
                        "job_id": job.id,
                    }
                    all_jobs.append(job_dict)
                if recent_jobs:
                    sources.append("Database (Recent)")
            except Exception as e:
                logger.error(f"Error fetching recent jobs: {str(e)}")
        
        # Return database results immediately (don't wait for external APIs)
        logger.info(f"Returning {len(all_jobs)} jobs from database immediately")
        result = {
            "jobs": all_jobs[:request.limit],
            "count": len(all_jobs[:request.limit]),
            "sources": sources if sources else ["Database"]
        }
        
        # Optionally try external APIs in background (don't wait for response)
        # This is async and won't block the return
        if len(all_jobs) < request.limit:
            try:
                logger.info("Trying external APIs in background (won't block response)...")
                # Start external API search in background (fire and forget)
                import asyncio
                asyncio.create_task(
                    asyncio.to_thread(
                        lambda: job_aggregator.search_jobs(
                            keywords=request.keywords,
                            job_titles=request.job_titles,
                            location=request.location,
                            limit=min(20, request.limit - len(all_jobs))
                        )
                    )
                )
            except Exception as e:
                logger.info(f"External API background search not started: {str(e)}")
        
        return result
    except Exception as e:
        logger.error(f"Error searching jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search jobs: {str(e)}"
        )


# ==================== INVESTMENT PLATFORM ENDPOINTS ====================

@router.get("/api/startups/list")
async def list_startups(
    skip: int = 0,
    limit: int = 100,
    sector: Optional[str] = None,
    min_credibility: float = 0.0,
    db: Session = Depends(get_db)
):
    """List verified startups available for investment."""
    try:
        startups = startup_verification.list_verified_startups(
            skip=skip,
            limit=limit,
            sector=sector,
            min_credibility=min_credibility,
            db=db
        )
        return {"startups": startups, "count": len(startups)}
    except Exception as e:
        logger.error(f"Error listing startups: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list startups: {str(e)}"
        )


@router.get("/api/startups/verify/{startup_id}")
async def verify_startup_endpoint(startup_id: str, db: Session = Depends(get_db)):
    """Verify a startup on the blockchain."""
    try:
        verification = startup_verification.verify_startup(startup_id, db)
        return verification
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error verifying startup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify startup: {str(e)}"
        )


@router.get("/api/startups/{startup_id}")
async def get_startup_details_endpoint(startup_id: str, db: Session = Depends(get_db)):
    """Get detailed startup information with verification proof."""
    try:
        details = startup_verification.get_startup_details(startup_id, db)
        return details
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting startup details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get startup details: {str(e)}"
        )


@router.get("/api/startups/by-founder/{founder_id}")
async def get_startup_by_founder_endpoint(founder_id: int, db: Session = Depends(get_db)):
    """Get startup information by founder/user ID."""
    try:
        # Find startup by founder_id
        startup = db.query(Startup).filter(Startup.founder_id == founder_id).first()
        if not startup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No startup found for founder {founder_id}"
            )
        
        # Calculate total investments
        total_investments_result = db.query(func.sum(Investment.amount)).filter(
            Investment.startup_id == startup.id
        ).scalar()
        total_investments = float(total_investments_result) if total_investments_result else 0.0
        
        # Get founder info
        founder = db.query(User).filter(User.id == founder_id).first()
        
        return {
            "id": startup.id,
            "startup_id": startup.startup_id,
            "name": startup.name,
            "sector": startup.sector,
            "country": startup.country,
            "description": startup.description,
            "funding_goal": startup.funding_goal,
            "pitch_deck_url": startup.pitch_deck_url,
            "credibility_score": startup.credibility_score,
            "employees_verified": startup.employees_verified,
            "transaction_signature": startup.transaction_signature,
            "website": startup.website,
            "contact_email": startup.contact_email,
            "phone": startup.phone,
            "address": startup.address,
            "year_founded": startup.year_founded,
            "team_size": startup.team_size,
            "mission": startup.mission,
            "vision": startup.vision,
            "products_services": startup.products_services,
            "total_investments": total_investments,
            "verified": startup.transaction_signature is not None,
            "on_chain": startup.transaction_signature is not None,
            "founder": {
                "id": founder.id if founder else None,
                "name": founder.full_name if founder else None,
                "email": founder.email if founder else None
            },
            "created_at": startup.created_at.isoformat() if startup.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting startup by founder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get startup: {str(e)}"
        )


class StartupRegisterRequest(BaseModel):
    name: str
    sector: str
    country: Optional[str] = None
    year_founded: Optional[int] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    mission: Optional[str] = None
    vision: Optional[str] = None
    description: Optional[str] = None
    products_services: Optional[str] = None
    funding_goal: Optional[float] = None
    pitch_deck_url: Optional[str] = None
    team_size: Optional[int] = 1
    wallet_address: str


@router.post("/api/startups/register")
async def register_startup_endpoint(
    request: StartupRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new startup."""
    try:
        logger.info(f"Registering startup: {request.name}")
        
        # Find founder by wallet address
        founder = db.query(User).filter(User.wallet_address == request.wallet_address).first()
        if not founder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with wallet address {request.wallet_address} not found"
            )
        
        # Check if user already has a startup
        existing_startup = db.query(Startup).filter(Startup.founder_id == founder.id).first()
        if existing_startup:
            # Calculate total investments for existing startup
            total_investments_result = db.query(func.sum(Investment.amount)).filter(
                Investment.startup_id == existing_startup.id
            ).scalar()
            total_investments = float(total_investments_result) if total_investments_result else 0.0
            
            # Return existing startup data
            return {
                "id": existing_startup.id,
                "startup_id": existing_startup.startup_id,
                "name": existing_startup.name,
                "sector": existing_startup.sector,
                "transaction_signature": existing_startup.transaction_signature,
                "verified": existing_startup.transaction_signature is not None,
                "on_chain": existing_startup.transaction_signature is not None,
                "total_investments": total_investments,
                "funding_goal": existing_startup.funding_goal,
                "already_exists": True,
                "message": "You already have a registered startup"
            }
        
        # Register startup on blockchain
        startup_client = StartupClient()
        blockchain_result = None
        blockchain_startup_id = None
        transaction_signature = None
        
        try:
            blockchain_result = startup_client.register_startup(
                startup_name=request.name,
                sector=request.sector,
                founder_address=request.wallet_address
            )
            blockchain_startup_id = blockchain_result.get("startup_id")
            transaction_signature = blockchain_result.get("transaction_signature")
            logger.info(f"Startup registered on blockchain: {blockchain_startup_id}")
        except Exception as e:
            logger.warning(f"Failed to register startup on blockchain: {str(e)}")
            # Generate fallback startup_id if blockchain fails
            import time
            blockchain_startup_id = f"STARTUP-{founder.id}-{int(time.time())}"
            transaction_signature = None
        
        # Create startup in database
        startup = Startup(
            founder_id=founder.id,
            startup_id=blockchain_startup_id,
            name=request.name,
            sector=request.sector,
            country=request.country,
            year_founded=request.year_founded,
            website=request.website,
            contact_email=request.contact_email,
            phone=request.phone,
            address=request.address,
            mission=request.mission,
            vision=request.vision,
            description=request.description,
            products_services=request.products_services,
            funding_goal=request.funding_goal,
            pitch_deck_url=request.pitch_deck_url,
            team_size=request.team_size,
            transaction_signature=transaction_signature,
            credibility_score=0.0,
            employees_verified=0
        )
        
        db.add(startup)
        db.commit()
        db.refresh(startup)
        
        logger.info(f"Startup registered successfully: {startup.id}, startup_id: {startup.startup_id}")
        
        return {
            "id": startup.id,
            "startup_id": startup.startup_id,
            "name": startup.name,
            "sector": startup.sector,
            "transaction_signature": startup.transaction_signature,
            "verified": transaction_signature is not None,
            "on_chain": transaction_signature is not None,
            "message": "Startup registered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering startup: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register startup: {str(e)}"
        )


class USDCInvestmentRequest(BaseModel):
    investor_id: int
    startup_id: str
    amount_usdc: float


@router.post("/api/investments/usdc/send")
async def send_usdc_investment_endpoint(
    request: USDCInvestmentRequest,
    db: Session = Depends(get_db)
):
    """Send USDC investment to a startup."""
    try:
        result = usdc_transactions.send_usdc_investment(
            investor_id=request.investor_id,
            startup_id=request.startup_id,
            amount_usdc=request.amount_usdc,
            db=db
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error sending USDC investment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send investment: {str(e)}"
        )


@router.get("/api/investments/portfolio/{investor_id}")
async def get_portfolio_endpoint(investor_id: int, db: Session = Depends(get_db)):
    """Get investor portfolio with all investments."""
    try:
        portfolio = investor_portfolio.get_portfolio(investor_id, db)
        return portfolio
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting portfolio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get portfolio: {str(e)}"
        )


@router.get("/api/investments/startup/{startup_id}")
async def get_startup_investments_endpoint(startup_id: str, db: Session = Depends(get_db)):
    """Get all investments for a specific startup."""
    try:
        investments = investor_portfolio.get_startup_investments(startup_id, db)
        return {"investments": investments, "count": len(investments)}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting startup investments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get startup investments: {str(e)}"
        )

