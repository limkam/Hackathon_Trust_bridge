from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.utils.logger import logger
from app.core.config import settings
import re


class AIService:
    """Advanced AI service for CV generation with market analysis, ATS optimization, and job tailoring."""
    
    def __init__(self):
        self.mistral_key = settings.MISTRAL_API_KEY or settings.OPENAI_API_KEY  # Backward compatibility
        # Industry keywords for market analysis
        self.industry_keywords = {
            "Technology": ["software development", "cloud computing", "agile", "devops", "api", "microservices"],
            "Healthcare": ["patient care", "medical records", "HIPAA", "clinical", "healthcare systems"],
            "Finance": ["financial analysis", "risk management", "compliance", "accounting", "audit"],
            "Education": ["curriculum development", "pedagogy", "student engagement", "assessment"],
            "Agriculture": ["sustainable farming", "crop management", "agribusiness", "rural development"],
        }
    
    def analyze_job_market(self, db: Session, sector: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze job market trends, required skills, and keywords.
        
        Returns:
            Market analysis with trending skills, keywords, and requirements
        """
        logger.info(f"Analyzing job market for sector: {sector}")
        
        from app.db.models import Job
        
        # Get all jobs or filter by sector
        query = db.query(Job)
        if sector:
            from app.db.models import Startup
            query = query.join(Job.startup).filter(Startup.sector.ilike(f"%{sector}%"))
        
        jobs = query.all()
        
        # Extract skills and keywords from job descriptions
        all_skills = []
        all_keywords = []
        
        for job in jobs:
            all_skills.extend(job.skills_required or [])
            # Extract keywords from description
            description_lower = job.description.lower()
            keywords = re.findall(r'\b[a-z]{4,}\b', description_lower)
            all_keywords.extend(keywords)
        
        # Count frequency
        skill_freq = {}
        for skill in all_skills:
            skill_lower = skill.lower()
            skill_freq[skill_lower] = skill_freq.get(skill_lower, 0) + 1
        
        keyword_freq = {}
        for keyword in all_keywords:
            if len(keyword) > 3:  # Filter short words
                keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        # Get top skills and keywords
        top_skills = sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:15]
        
        # Add industry-specific keywords
        industry_keywords_list = self.industry_keywords.get(sector or "Technology", [])
        
        analysis = {
            "sector": sector,
            "total_jobs_analyzed": len(jobs),
            "trending_skills": [{"skill": skill, "frequency": freq} for skill, freq in top_skills],
            "trending_keywords": [{"keyword": kw, "frequency": freq} for kw, freq in top_keywords],
            "industry_keywords": industry_keywords_list,
            "recommendations": self._generate_market_recommendations(top_skills, industry_keywords_list)
        }
        
        logger.info(f"Market analysis complete: {len(top_skills)} trending skills identified")
        return analysis
    
    def extract_skills_and_achievements(
        self,
        experience: list,
        projects: list,
        education: list
    ) -> Dict[str, Any]:
        """
        Extract hard skills, soft skills, tools, and quantifiable achievements.
        
        Returns:
            Extracted skills, achievements, and impact statements
        """
        logger.info("Extracting skills and achievements from user data")
        
        hard_skills = set()
        soft_skills = set()
        tools = set()
        achievements = []
        impact_statements = []
        
        # Extract from experience
        for exp in experience:
            description = exp.get("description", "").lower()
            title = exp.get("title", "").lower()
            
            # Extract hard skills (technical terms)
            tech_keywords = ["python", "javascript", "react", "node", "sql", "api", "database",
                           "management", "analysis", "design", "development", "marketing",
                           "sales", "finance", "accounting", "healthcare", "education"]
            for keyword in tech_keywords:
                if keyword in description or keyword in title:
                    hard_skills.add(keyword.title())
            
            # Extract soft skills
            soft_keywords = ["leadership", "teamwork", "communication", "collaboration",
                           "problem-solving", "critical thinking", "adaptability"]
            for keyword in soft_keywords:
                if keyword in description:
                    soft_skills.add(keyword.title())
            
            # Extract quantifiable achievements (numbers, percentages)
            numbers = re.findall(r'(\d+%?|\$\d+[KMB]?|\d+\+|\d+[KMB]?)', exp.get("description", ""))
            if numbers:
                achievements.append({
                    "context": exp.get("title", ""),
                    "metrics": numbers,
                    "description": exp.get("description", "")
                })
            
            # Extract impact statements
            impact_verbs = ["increased", "decreased", "improved", "reduced", "achieved",
                          "delivered", "led", "managed", "created", "developed"]
            for verb in impact_verbs:
                if verb in description:
                    # Extract sentence with impact verb
                    sentences = re.split(r'[.!?]', description)
                    for sentence in sentences:
                        if verb in sentence.lower():
                            impact_statements.append(sentence.strip())
                            break
        
        # Extract from projects
        for project in projects:
            if isinstance(project, str):
                project_lower = project.lower()
                # Extract technical terms
                for keyword in ["python", "javascript", "react", "app", "system", "platform"]:
                    if keyword in project_lower:
                        hard_skills.add(keyword.title())
        
        # Extract tools from experience descriptions
        tools_keywords = ["excel", "word", "powerpoint", "photoshop", "figma", "jira",
                        "slack", "trello", "github", "git", "docker", "kubernetes"]
        for exp in experience:
            desc_lower = exp.get("description", "").lower()
            for tool in tools_keywords:
                if tool in desc_lower:
                    tools.add(tool.title())
        
        return {
            "hard_skills": sorted(list(hard_skills)),
            "soft_skills": sorted(list(soft_skills)),
            "tools": sorted(list(tools)),
            "achievements": achievements[:10],  # Top 10
            "impact_statements": impact_statements[:5],  # Top 5
            "hidden_achievements": self._identify_hidden_achievements(experience)
        }
    
    def tailor_cv_to_job(
        self,
        cv_data: Dict[str, Any],
        job_description: str,
        job_skills: List[str],
        job_title: str
    ) -> Dict[str, Any]:
        """
        Tailor CV to a specific job listing.
        
        Returns:
            Tailored CV with job-specific keywords and emphasized experiences
        """
        logger.info(f"Tailoring CV for job: {job_title}")
        
        # Extract keywords from job description
        job_keywords = self._extract_keywords_from_job(job_description, job_skills)
        
        # Create tailored CV
        tailored_cv = cv_data.copy()
        
        # Enhance summary with job keywords
        original_summary = tailored_cv.get("summary", "")
        tailored_summary = self._enhance_summary_with_keywords(original_summary, job_keywords, job_title)
        tailored_cv["summary"] = tailored_summary
        
        # Reorder and emphasize relevant experience
        experience = tailored_cv.get("work_experience", [])
        tailored_experience = self._prioritize_relevant_experience(experience, job_keywords, job_skills)
        tailored_cv["work_experience"] = tailored_experience
        
        # Enhance skills section with job-relevant skills first
        skills = tailored_cv.get("personal_skills", {})
        job_related_skills = skills.get("job_related_skills", [])
        prioritized_skills = self._prioritize_skills(job_related_skills, job_skills)
        tailored_cv["personal_skills"]["job_related_skills"] = prioritized_skills
        
        # Add job-specific recommendations
        tailored_cv["job_tailoring"] = {
            "target_job": job_title,
            "keywords_added": job_keywords[:10],
            "skills_emphasized": [s for s in job_skills if s.lower() in [sk.lower() for sk in job_related_skills]][:5],
            "recommendations": self._generate_job_specific_recommendations(cv_data, job_keywords, job_skills)
        }
        
        logger.info(f"CV tailored for {job_title}: {len(job_keywords)} keywords integrated")
        return tailored_cv
    
    def optimize_for_ats(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize CV for Applicant Tracking Systems (ATS).
        
        Returns:
            ATS-optimized CV with proper formatting and keywords
        """
        logger.info("Optimizing CV for ATS compatibility")
        
        optimized_cv = cv_data.copy()
        
        # Ensure ATS-friendly section headers
        ats_headers = {
            "work_experience": "WORK EXPERIENCE",
            "education": "EDUCATION",
            "skills": "SKILLS",
            "summary": "PROFESSIONAL SUMMARY"
        }
        
        # Remove special characters that ATS might not parse
        summary = optimized_cv.get("summary", "")
        optimized_summary = re.sub(r'[^\w\s.,;:()\-]', '', summary)
        optimized_cv["summary"] = optimized_summary
        
        # Ensure skills are in plain text format (not nested objects)
        skills = optimized_cv.get("personal_skills", {})
        if isinstance(skills, dict):
            # Flatten skills for ATS
            all_skills = []
            if skills.get("job_related_skills"):
                all_skills.extend(skills["job_related_skills"])
            if skills.get("computer_skills"):
                all_skills.extend(skills["computer_skills"])
            optimized_cv["ats_skills"] = ", ".join(all_skills)
        
        # Add ATS optimization metadata
        optimized_cv["ats_optimized"] = {
            "keyword_density": self._calculate_keyword_density(optimized_cv),
            "section_completeness": self._check_section_completeness(optimized_cv),
            "formatting_score": self._check_ats_formatting(optimized_cv),
            "recommendations": self._generate_ats_recommendations(optimized_cv)
        }
        
        logger.info("ATS optimization complete")
        return optimized_cv
    
    def enhance_language(self, text: str, section: str = "experience") -> str:
        """
        Enhance text with powerful, professional language.
        
        Uses OpenAI API if available, otherwise falls back to rule-based enhancement.
        """
        if not text:
            return text
        
        # Try Mistral AI API if key is available
        if self.mistral_key:
            try:
                from mistralai import Mistral
                client = Mistral(api_key=self.mistral_key)
                
                prompt = f"""Rewrite the following CV {section} description to be more professional, impactful, and ATS-friendly. 
Use strong action verbs, quantify achievements where possible, and maintain a professional tone.
Remove first-person pronouns (I, my, me) and make it concise.

Original text:
{text}

Enhanced version (only return the enhanced text, no explanations):"""
                
                response = client.chat.complete(
                    model="mistral-small-latest",
                    messages=[
                        {"role": "system", "content": "You are a professional CV writing assistant. Rewrite text to be more impactful and professional."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                
                enhanced = response.choices[0].message.content.strip()
                if enhanced:
                    logger.info(f"AI-enhanced text for {section} section (Mistral AI)")
                    return enhanced
            except ImportError:
                logger.warning("Mistral AI library not installed, using rule-based enhancement")
            except Exception as e:
                logger.error(f"Mistral AI API error: {str(e)}, falling back to rule-based enhancement")
        
        # Fallback to rule-based enhancement
        weak_verbs = {
            "worked": "executed",
            "helped": "collaborated to",
            "did": "delivered",
            "made": "created",
            "got": "achieved",
            "did stuff": "implemented",
            "was responsible for": "spearheaded",
            "assisted": "contributed to",
            "worked on": "developed and delivered",
            "helped with": "collaborated to achieve",
            "i did": "delivered",
            "my job was": "key responsibilities included"
        }
        
        enhanced = text
        for weak, strong in weak_verbs.items():
            enhanced = re.sub(rf'\b{re.escape(weak)}\b', strong, enhanced, flags=re.IGNORECASE)
        
        # Add quantifiers if missing
        if section == "experience" and not re.search(r'\d+', enhanced):
            if "managed" in enhanced.lower():
                enhanced = enhanced.replace("managed", "managed and optimized")
            if "led" in enhanced.lower():
                enhanced = enhanced.replace("led", "led and delivered")
        
        # Ensure professional tone - remove first person
        enhanced = re.sub(r'\bI\s+', '', enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r'\bi\s+', '', enhanced)
        enhanced = enhanced.replace("my ", "the ").replace("My ", "The ")
        enhanced = enhanced.replace("me ", "").replace("Me ", "")
        
        return enhanced.strip()
    
    def highlight_strengths(
        self,
        cv_data: Dict[str, Any],
        job_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Identify and highlight user's key strengths.
        
        Returns:
            CV with highlighted strengths and leadership moments
        """
        logger.info("Identifying and highlighting user strengths")
        
        highlighted_cv = cv_data.copy()
        strengths = {
            "leadership_moments": [],
            "teamwork_examples": [],
            "technical_competencies": [],
            "unique_achievements": []
        }
        
        # Analyze experience for strengths
        experience = cv_data.get("work_experience", [])
        for exp in experience:
            desc = exp.get("description", "").lower()
            title = exp.get("title", "").lower()
            
            # Leadership moments
            if any(word in desc for word in ["led", "managed", "supervised", "directed", "headed"]):
                strengths["leadership_moments"].append({
                    "role": exp.get("title", ""),
                    "example": exp.get("description", "")
                })
            
            # Teamwork examples
            if any(word in desc for word in ["collaborated", "team", "worked with", "coordinated"]):
                strengths["teamwork_examples"].append({
                    "role": exp.get("title", ""),
                    "example": exp.get("description", "")
                })
            
            # Technical competencies
            tech_keywords = ["python", "javascript", "react", "sql", "api", "system", "platform"]
            if any(keyword in desc for keyword in tech_keywords):
                strengths["technical_competencies"].append(exp.get("title", ""))
        
        # Analyze projects for unique achievements
        projects = cv_data.get("additional_info", {}).get("projects", [])
        for project in projects[:3]:  # Top 3 projects
            if isinstance(project, str) and len(project) > 20:
                strengths["unique_achievements"].append(project)
        
        # Add strengths section to CV
        highlighted_cv["strengths_analysis"] = strengths
        highlighted_cv["highlighted_summary"] = self._create_highlighted_summary(
            cv_data.get("summary", ""),
            strengths
        )
        
        logger.info(f"Identified {len(strengths['leadership_moments'])} leadership moments")
        return highlighted_cv
    
    def generate_cv(
        self,
        user_data: Dict[str, Any],
        certificates: list = None,  # Deprecated - use education list instead
        experience: list = None,
        education: list = None,
        skills: Dict[str, Any] = None,
        awards: list = None,
        publications: list = None,
        projects: list = None,
        memberships: list = None,
        job_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Generate a professional CV with AI enhancements.
        
        If job_id is provided, the CV will be tailored to that specific job.
        """
        logger.info(f"Generating AI-enhanced CV for user: {user_data.get('full_name')}")
        
        # Step 1: Extract skills and achievements
        extracted_data = self.extract_skills_and_achievements(experience, projects or [], education or [])
        
        # Step 2: Enhance experience descriptions with powerful language
        enhanced_experience = []
        for exp in experience:
            enhanced_exp = exp.copy()
            enhanced_exp["description"] = self.enhance_language(exp.get("description", ""), "experience")
            enhanced_experience.append(enhanced_exp)
        
        # Step 3: Build base CV structure
        cv_data = {
            "personal_info": {
                "surname": user_data.get("surname", ""),
                "first_name": user_data.get("first_name", ""),
                "full_name": user_data.get("full_name", "") or f"{user_data.get('first_name', '')} {user_data.get('surname', '')}".strip(),
                "address": user_data.get("address", ""),
                "phone": user_data.get("phone", ""),
                "email": user_data.get("email", ""),
                "date_of_birth": user_data.get("date_of_birth", ""),
                "nationality": user_data.get("nationality", ""),
                "gender": user_data.get("gender", ""),
                "wallet_address": user_data.get("wallet_address", ""),
                "photo_url": user_data.get("photo_url")
            },
            "summary": self._generate_enhanced_summary(user_data, enhanced_experience, skills or {}, extracted_data),
            "education": self._format_education_europass(certificates or [], education or []),
            "work_experience": enhanced_experience,
            "personal_skills": self._format_skills_europass(skills or {}),
            "additional_info": {
                "awards": awards or [],
                "publications": publications or [],
                "projects": projects or [],
                "memberships": memberships or []
            },
            "blockchain_verification": {
                "verified_certificates": 0,  # Certificates removed - using education from CV
                "on_chain_proof": True
            },
            "extracted_data": extracted_data
        }
        
        # Step 4: Tailor to specific job if job_id provided
        if job_id and db:
            from app.db.models import Job
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                cv_data = self.tailor_cv_to_job(
                    cv_data,
                    job.description,
                    job.skills_required or [],
                    job.title
                )
        
        # Step 5: Optimize for ATS
        cv_data = self.optimize_for_ats(cv_data)
        
        # Step 6: Highlight strengths
        job_reqs = None
        if job_id and db:
            from app.db.models import Job
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job_reqs = {
                    "skills": job.skills_required or [],
                    "title": job.title
                }
        cv_data = self.highlight_strengths(cv_data, job_reqs)
        
        # Step 7: Calculate AI score
        cv_data["ai_score"] = self._calculate_cv_score(cv_data)
        
        logger.info(f"AI-enhanced CV generated with score: {cv_data['ai_score']}")
        return cv_data
    
    # Helper methods
    
    def _generate_market_recommendations(self, top_skills: List[tuple], industry_keywords: List[str]) -> List[str]:
        """Generate market-based recommendations."""
        recommendations = []
        
        if top_skills:
            top_3_skills = [skill for skill, _ in top_skills[:3]]
            recommendations.append(f"Emphasize these trending skills: {', '.join(top_3_skills)}")
        
        if industry_keywords:
            recommendations.append(f"Include industry keywords: {', '.join(industry_keywords[:5])}")
        
        recommendations.append("Quantify achievements with numbers and percentages")
        recommendations.append("Use action verbs: Led, Delivered, Achieved, Optimized")
        
        return recommendations
    
    def _extract_keywords_from_job(self, job_description: str, job_skills: List[str]) -> List[str]:
        """Extract keywords from job description."""
        keywords = set()
        
        # Add skills as keywords
        keywords.update([skill.lower() for skill in job_skills])
        
        # Extract important words from description (4+ characters)
        words = re.findall(r'\b[a-z]{4,}\b', job_description.lower())
        
        # Filter common words
        common_words = {"this", "that", "with", "from", "will", "have", "been", "work", "team"}
        important_words = [w for w in words if w not in common_words]
        
        # Count frequency and get top keywords
        word_freq = {}
        for word in important_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:15]
        keywords.update([word for word, _ in top_words])
        
        return list(keywords)
    
    def _enhance_summary_with_keywords(self, summary: str, keywords: List[str], job_title: str) -> str:
        """Enhance summary with job-specific keywords."""
        if not summary:
            return f"Results-driven professional seeking {job_title} position with expertise in {', '.join(keywords[:3])}."
        
        # Try to naturally incorporate keywords
        summary_lower = summary.lower()
        missing_keywords = [kw for kw in keywords[:5] if kw not in summary_lower]
        
        if missing_keywords:
            # Add missing keywords naturally
            summary += f" Proficient in {', '.join(missing_keywords[:3])}."
        
        return summary
    
    def _prioritize_relevant_experience(self, experience: list, keywords: List[str], job_skills: List[str]) -> list:
        """Reorder experience to prioritize most relevant roles."""
        def relevance_score(exp):
            score = 0
            desc_lower = exp.get("description", "").lower()
            title_lower = exp.get("title", "").lower()
            
            # Check for keyword matches
            for keyword in keywords:
                if keyword in desc_lower or keyword in title_lower:
                    score += 2
            
            # Check for skill matches
            for skill in job_skills:
                if skill.lower() in desc_lower or skill.lower() in title_lower:
                    score += 3
            
            return score
        
        # Sort by relevance
        sorted_experience = sorted(experience, key=relevance_score, reverse=True)
        return sorted_experience
    
    def _prioritize_skills(self, user_skills: List[str], job_skills: List[str]) -> List[str]:
        """Reorder skills to prioritize job-relevant skills."""
        relevant_skills = []
        other_skills = []
        
        job_skills_lower = [s.lower() for s in job_skills]
        
        for skill in user_skills:
            if any(js in skill.lower() for js in job_skills_lower):
                relevant_skills.append(skill)
            else:
                other_skills.append(skill)
        
        return relevant_skills + other_skills
    
    def _generate_job_specific_recommendations(
        self,
        cv_data: Dict[str, Any],
        keywords: List[str],
        job_skills: List[str]
    ) -> List[str]:
        """Generate job-specific recommendations."""
        recommendations = []
        
        # Check if keywords are in CV
        cv_text = str(cv_data).lower()
        missing_keywords = [kw for kw in keywords[:10] if kw not in cv_text]
        
        if missing_keywords:
            recommendations.append(f"Add these keywords: {', '.join(missing_keywords[:5])}")
        
        # Check skills match
        user_skills = cv_data.get("personal_skills", {}).get("job_related_skills", [])
        user_skills_lower = [s.lower() for s in user_skills]
        missing_skills = [js for js in job_skills if js.lower() not in user_skills_lower]
        
        if missing_skills:
            recommendations.append(f"Consider adding these skills: {', '.join(missing_skills[:3])}")
        
        return recommendations
    
    def _calculate_keyword_density(self, cv_data: Dict[str, Any]) -> float:
        """Calculate keyword density for ATS optimization."""
        # Simple keyword density calculation
        cv_text = str(cv_data).lower()
        total_words = len(cv_text.split())
        if total_words == 0:
            return 0.0
        
        # Count technical keywords
        tech_keywords = ["management", "development", "analysis", "design", "implementation"]
        keyword_count = sum(1 for kw in tech_keywords if kw in cv_text)
        
        return round((keyword_count / total_words) * 100, 2) if total_words > 0 else 0.0
    
    def _check_section_completeness(self, cv_data: Dict[str, Any]) -> Dict[str, bool]:
        """Check if all ATS-required sections are present."""
        return {
            "summary": bool(cv_data.get("summary")),
            "experience": len(cv_data.get("work_experience", [])) > 0,
            "education": len(cv_data.get("education", [])) > 0,
            "skills": bool(cv_data.get("personal_skills", {}).get("job_related_skills"))
        }
    
    def _check_ats_formatting(self, cv_data: Dict[str, Any]) -> float:
        """Check ATS formatting compliance."""
        score = 100.0
        
        # Check for special characters that ATS might not parse
        cv_text = str(cv_data)
        if re.search(r'[^\w\s.,;:()\-\n]', cv_text):
            score -= 10  # Penalize special characters
        
        # Check section headers
        required_sections = ["summary", "experience", "education", "skills"]
        cv_text_lower = cv_text.lower()
        for section in required_sections:
            if section not in cv_text_lower:
                score -= 15
        
        return max(0, score)
    
    def _generate_ats_recommendations(self, cv_data: Dict[str, Any]) -> List[str]:
        """Generate ATS optimization recommendations."""
        recommendations = []
        
        completeness = self._check_section_completeness(cv_data)
        if not completeness.get("summary"):
            recommendations.append("Add a professional summary section")
        if not completeness.get("experience"):
            recommendations.append("Include work experience section")
        if not completeness.get("skills"):
            recommendations.append("List your skills clearly")
        
        formatting_score = self._check_ats_formatting(cv_data)
        if formatting_score < 90:
            recommendations.append("Remove special characters and use plain text formatting")
        
        return recommendations
    
    def _identify_hidden_achievements(self, experience: list) -> List[str]:
        """Identify achievements that user might not have highlighted."""
        hidden = []
        
        for exp in experience:
            desc = exp.get("description", "")
            # Look for quantifiable results
            if re.search(r'\d+', desc):
                hidden.append(f"{exp.get('title', 'Role')}: {desc[:100]}")
        
        return hidden[:5]
    
    def _create_highlighted_summary(self, original_summary: str, strengths: Dict[str, Any]) -> str:
        """Create a summary that highlights key strengths."""
        if not original_summary:
            return ""
        
        # Add strength highlights if not already present
        if strengths.get("leadership_moments") and "leadership" not in original_summary.lower():
            original_summary += " Proven leadership experience."
        
        if strengths.get("technical_competencies") and "technical" not in original_summary.lower():
            original_summary += " Strong technical background."
        
        return original_summary
    
    def _generate_enhanced_summary(
        self,
        user_data: Dict[str, Any],
        experience: list,
        skills: Dict[str, Any],
        extracted_data: Dict[str, Any]
    ) -> str:
        """Generate enhanced professional summary with extracted achievements."""
        role = user_data.get("role", "professional")
        years_exp = len(experience) if experience else 0
        
        # Use extracted skills
        job_skills = skills.get("job_related_skills", []) or []
        hard_skills = extracted_data.get("hard_skills", [])[:3]
        top_skills = ", ".join(hard_skills) if hard_skills else ", ".join(job_skills[:3]) if job_skills else "various skills"
        
        # Use impact statements if available
        impact = extracted_data.get("impact_statements", [])
        impact_text = ""
        if impact:
            impact_text = f" {impact[0][:100]}"
        
        summaries = {
            "student": f"Results-driven student with verified blockchain credentials and expertise in {top_skills}.{impact_text} Seeking opportunities to apply academic knowledge in real-world projects.",
            "founder": f"Entrepreneurial founder with {years_exp} years of experience in building and scaling startups. Verified credentials and expertise in {top_skills}.{impact_text}",
            "investor": f"Experienced investor with a track record of supporting innovative startups. Expertise in {top_skills} and blockchain technology.",
            "employer": f"Results-driven professional with {years_exp} years in the industry. Strong background in {top_skills} and verified credentials.{impact_text}"
        }
        
        return summaries.get(role, f"Professional with expertise in {top_skills}.{impact_text}")
    
    def _format_education_europass(self, certificates: list, additional_education: list) -> list:
        """Format education section in Europass format."""
        education = []
        
        for cert in certificates:
            is_verified = cert.get("verified") == "verified"
            education.append({
                "dates": str(cert.get("graduation_year", "")),
                "title": cert.get("major", "Degree"),
                "organization": cert.get("university", ""),
                "level": "Higher Education",
                "verified": is_verified,
                "blockchain_proof": cert.get("transaction_signature") if is_verified else None
            })
        
        for edu in additional_education:
            education.append({
                "dates": edu.get("dates", ""),
                "title": edu.get("title", ""),
                "organization": edu.get("institution", ""),
                "level": edu.get("level", ""),
                "verified": False
            })
        
        return sorted(education, key=lambda x: x.get("dates", ""), reverse=True)
    
    def _format_skills_europass(self, skills: Dict[str, Any]) -> Dict[str, Any]:
        """Format skills in Europass format."""
        return {
            "mother_tongue": skills.get("mother_tongue", ""),
            "other_languages": skills.get("other_languages", []),
            "social_skills": skills.get("social_skills", []),
            "organizational_skills": skills.get("organizational_skills", []),
            "job_related_skills": skills.get("job_related_skills", []),
            "computer_skills": skills.get("computer_skills", []),
            "driving_licence": skills.get("driving_licence", "")
        }
    
    def _calculate_cv_score(self, cv_data: Dict[str, Any]) -> float:
        """Calculate comprehensive CV quality score."""
        score = 0.0
        
        # Personal info (20 points)
        personal = cv_data.get("personal_info", {})
        if personal.get("full_name"):
            score += 5
        if personal.get("email"):
            score += 5
        if personal.get("wallet_address"):
            score += 5
        if personal.get("phone"):
            score += 5
        
        # Summary quality (20 points)
        summary = cv_data.get("summary", "")
        if summary and len(summary) > 50:
            score += 15
        if "results" in summary.lower() or "achieved" in summary.lower():
            score += 5
        
        # Education (20 points)
        education = cv_data.get("education", [])
        if education:
            score += min(20, len(education) * 7)
        
        # Experience with impact (25 points)
        experience = cv_data.get("work_experience", [])
        if experience:
            score += min(20, len(experience) * 7)
            # Bonus for quantified achievements
            exp_text = str(experience).lower()
            if re.search(r'\d+%?|\$\d+', exp_text):
                score += 5
        
        # Skills (10 points)
        skills = cv_data.get("personal_skills", {}).get("job_related_skills", [])
        if skills:
            score += min(10, len(skills) * 2)
        
        # Blockchain verification removed - no longer part of core solution
        
        # ATS optimization bonus (5 points)
        if cv_data.get("ats_optimized"):
            score += 5
        
        return round(min(100, score), 2)
    
    def suggest_powerful_language(self, section: str, content: str) -> List[str]:
        """Suggest powerful language alternatives."""
        suggestions = {
            "summary": [
                "Results-driven professional with proven track record",
                "Dynamic leader with expertise in",
                "Strategic thinker with demonstrated success in",
                "Innovative problem-solver specializing in",
            ],
            "experience": [
                "Led and executed projects that increased efficiency by 30%",
                "Spearheaded initiatives resulting in measurable business growth",
                "Delivered measurable results including",
                "Collaborated cross-functionally to achieve",
                "Optimized processes leading to cost savings",
            ],
            "skills": [
                "Proficient in",
                "Expert-level knowledge of",
                "Advanced skills in",
                "Certified in",
            ],
        }
        return suggestions.get(section, [])
    
    def get_formatting_tips(self, section: str) -> List[str]:
        """Get formatting tips for CV sections."""
        tips = {
            "summary": [
                "Keep it concise (2-3 sentences)",
                "Highlight your key strengths",
                "Mention years of experience if relevant",
                "Include your career objective",
            ],
            "experience": [
                "Use bullet points for clarity",
                "Start with action verbs (Led, Delivered, Achieved)",
                "Quantify achievements with numbers and percentages",
                "Focus on results, not just duties",
            ],
            "skills": [
                "Group related skills together",
                "List most relevant skills first",
                "Include both technical and soft skills",
                "Be specific (e.g., 'Python' not 'Programming')",
            ],
        }
        return tips.get(section, [])
    
    def get_realtime_suggestions(self, section: str, current_text: str, industry: str = None) -> Dict[str, Any]:
        """
        Provide real-time AI suggestions as user types.
        
        Uses OpenAI API if available for better suggestions, otherwise uses rule-based analysis.
        """
        suggestions = {
            "improvements": [],
            "examples": [],
            "recommendations": []
        }
        
        if not current_text or len(current_text) < 10:
            return suggestions
        
        # Try Mistral AI API if key is available and text is substantial
        if self.mistral_key and len(current_text) > 20:
            try:
                from mistralai import Mistral
                client = Mistral(api_key=self.mistral_key)
                
                prompt = f"""Analyze this CV {section} text and provide specific suggestions:
1. Identify weak phrases that should be replaced with stronger alternatives
2. Suggest improvements for better impact
3. Provide recommendations for making it more professional

Text: {current_text}

Respond in JSON format:
{{
    "improvements": [{{"weak": "phrase to replace", "strong": "better alternative"}}],
    "recommendations": ["specific recommendation 1", "specific recommendation 2"]
}}"""
                
                response = client.chat.complete(
                    model="mistral-small-latest",
                    messages=[
                        {"role": "system", "content": "You are a professional CV writing assistant. Provide specific, actionable suggestions in JSON format."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.5
                )
                
                import json
                content = response.choices[0].message.content.strip()
                # Try to extract JSON from response
                try:
                    # If response is wrapped in markdown code blocks, extract it
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()
                    
                    ai_suggestions = json.loads(content)
                    suggestions["improvements"] = ai_suggestions.get("improvements", [])
                    suggestions["recommendations"] = ai_suggestions.get("recommendations", [])
                    logger.info(f"AI-generated suggestions for {section} section (Mistral AI)")
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse AI response as JSON: {content[:100]}")
                    # Fall through to rule-based suggestions
            except ImportError:
                logger.warning("Mistral AI library not installed, using rule-based suggestions")
            except Exception as e:
                logger.error(f"Mistral AI API error: {str(e)}, falling back to rule-based suggestions")
        
        # Fallback to rule-based analysis
        text_lower = current_text.lower()
        
        # Check for weak language
        weak_phrases = {
            "worked on": "Executed and delivered",
            "helped with": "Collaborated to achieve",
            "was responsible": "Spearheaded",
            "did some": "Implemented",
            "i did": "Delivered",
            "my job was": "Key responsibilities included",
            "worked": "Executed",
            "helped": "Collaborated",
            "made": "Created",
            "got": "Achieved"
        }
        
        for weak, strong in weak_phrases.items():
            if weak in text_lower and not any(imp.get("weak") == weak for imp in suggestions["improvements"]):
                suggestions["improvements"].append({
                    "weak": weak,
                    "strong": strong,
                    "context": f"Replace '{weak}' with '{strong}' for more impact"
                })
        
        # Check for missing quantifiers
        if section == "experience" and not re.search(r'\d+', current_text):
            if not any("quantify" in rec.lower() for rec in suggestions["recommendations"]):
                suggestions["recommendations"].append("Add numbers or percentages to quantify your achievements (e.g., 'increased sales by 30%', 'managed team of 5')")
        
        # Check for action verbs
        action_verbs = ["led", "delivered", "achieved", "created", "improved", "managed", "developed", "executed", "spearheaded"]
        has_action_verb = any(verb in text_lower for verb in action_verbs)
        if not has_action_verb and section == "experience":
            if not any("action verb" in rec.lower() for rec in suggestions["recommendations"]):
                suggestions["recommendations"].append("Start with an action verb (e.g., 'Led', 'Delivered', 'Achieved', 'Developed')")
        
        # Check for first person
        if re.search(r'\b(I|my|me)\b', current_text, re.IGNORECASE):
            suggestions["recommendations"].append("Remove first-person pronouns (I, my, me) for a more professional tone")
        
        # Industry-specific suggestions
        if industry:
            industry_examples = self._get_industry_examples(section, industry)
            suggestions["examples"].extend(industry_examples)
        
        return suggestions
    
    def _get_industry_examples(self, section: str, industry: str) -> List[str]:
        """Get industry-specific examples for a section."""
        examples = {
            "Technology": {
                "experience": [
                    "Developed scalable web applications using React and Node.js, serving 10,000+ daily users",
                    "Led a team of 5 developers to deliver a mobile app that increased user engagement by 40%",
                    "Optimized database queries reducing response time by 60%"
                ],
                "summary": [
                    "Software engineer with 3+ years of experience in full-stack development, specializing in React, Node.js, and cloud technologies",
                    "Results-driven developer with expertise in building scalable applications and leading cross-functional teams"
                ]
            },
            "Healthcare": {
                "experience": [
                    "Managed patient care for 50+ patients daily, ensuring compliance with medical protocols",
                    "Collaborated with multidisciplinary team to improve patient outcomes by 25%",
                    "Maintained accurate medical records using electronic health systems"
                ],
                "summary": [
                    "Dedicated healthcare professional with expertise in patient care and medical administration",
                    "Compassionate nurse with proven track record in improving patient satisfaction scores"
                ]
            },
            "Education": {
                "experience": [
                    "Developed and implemented curriculum for 120+ students, improving test scores by 30%",
                    "Led after-school programs that increased student participation by 50%",
                    "Collaborated with parents and administrators to enhance learning outcomes"
                ],
                "summary": [
                    "Passionate educator with expertise in curriculum development and student engagement",
                    "Dedicated teacher with proven ability to improve student performance and foster learning"
                ]
            }
        }
        
        return examples.get(industry, {}).get(section, [])
    
    def get_university_prompts(self) -> Dict[str, List[str]]:
        """Get prompts to help translate university experience into professional language."""
        return {
            "projects": [
                "What projects did you complete during your studies?",
                "Describe a major project or thesis you worked on",
                "What technical skills did you use in your projects?",
                "What problems did your projects solve?"
            ],
            "coursework": [
                "How did your coursework prepare you for this role?",
                "What relevant courses did you take?",
                "What practical skills did you gain from your courses?",
                "How does your academic background relate to this position?"
            ],
            "skills": [
                "What skills did you gain from your degree?",
                "What technical tools did you learn in university?",
                "What soft skills did you develop through group projects?",
                "What certifications or training did you complete?"
            ],
            "achievements": [
                "Did you receive any academic awards or honors?",
                "Were you part of any student organizations?",
                "Did you participate in any competitions or hackathons?",
                "What leadership roles did you have in university?"
            ]
        }
    
    def calculate_ats_score(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive ATS compatibility score.
        
        Returns:
            Score (0-100), issues, and specific fixes
        """
        score = 100
        issues = []
        fixes = []
        
        # Check section completeness (20 points)
        required_sections = ["summary", "work_experience", "education", "personal_skills"]
        missing_sections = [s for s in required_sections if not cv_data.get(s)]
        if missing_sections:
            score -= len(missing_sections) * 5
            issues.append(f"Missing sections: {', '.join(missing_sections)}")
            fixes.append(f"Add the following sections: {', '.join(missing_sections)}")
        
        # Check formatting (30 points)
        formatting_score = self._check_ats_formatting(cv_data)
        if formatting_score < 90:
            score -= (90 - formatting_score) * 0.3
            issues.append("Formatting issues detected")
            fixes.append("Remove special characters, use plain text formatting")
        
        # Check keywords (25 points)
        keyword_density = self._calculate_keyword_density(cv_data)
        if keyword_density < 2.0:
            score -= 10
            issues.append("Low keyword density")
            fixes.append("Add more industry-relevant keywords to your CV")
        
        # Check action verbs (15 points)
        experience = cv_data.get("work_experience", [])
        has_action_verbs = False
        for exp in experience:
            desc = exp.get("description", "").lower()
            if any(verb in desc for verb in ["led", "delivered", "achieved", "created", "improved"]):
                has_action_verbs = True
                break
        if not has_action_verbs and experience:
            score -= 15
            issues.append("Missing action verbs in experience descriptions")
            fixes.append("Start each bullet point with an action verb (Led, Delivered, Achieved)")
        
        # Check quantifiers (10 points)
        has_numbers = False
        for exp in experience:
            if re.search(r'\d+', exp.get("description", "")):
                has_numbers = True
                break
        if not has_numbers and experience:
            score -= 10
            issues.append("Missing quantifiable achievements")
            fixes.append("Add numbers, percentages, or metrics to your achievements")
        
        return {
            "score": max(0, min(100, int(score))),
            "issues": issues,
            "fixes": fixes,
            "formatting_score": formatting_score,
            "keyword_density": keyword_density,
            "recommendations": self._generate_ats_recommendations(cv_data)
        }
    
    def get_industry_template(self, industry: str) -> Dict[str, Any]:
        """Get industry-specific CV template structure."""
        templates = {
            "Technology": {
                "sections_order": ["summary", "technical_skills", "work_experience", "education", "projects", "certifications"],
                "emphasis": ["technical_skills", "projects"],
                "keywords": ["software development", "agile", "cloud computing", "api", "devops", "full-stack"]
            },
            "Healthcare": {
                "sections_order": ["summary", "work_experience", "education", "certifications", "skills"],
                "emphasis": ["work_experience", "certifications"],
                "keywords": ["patient care", "medical records", "HIPAA", "clinical", "healthcare systems"]
            },
            "Education": {
                "sections_order": ["summary", "education", "work_experience", "certifications", "skills"],
                "emphasis": ["education", "certifications"],
                "keywords": ["curriculum development", "pedagogy", "student engagement", "assessment"]
            },
            "Finance": {
                "sections_order": ["summary", "work_experience", "education", "certifications", "skills"],
                "emphasis": ["work_experience", "certifications"],
                "keywords": ["financial analysis", "risk management", "compliance", "accounting"]
            },
            "Agriculture": {
                "sections_order": ["summary", "work_experience", "education", "skills", "projects"],
                "emphasis": ["work_experience", "projects"],
                "keywords": ["sustainable farming", "crop management", "agribusiness", "rural development"]
            }
        }
        
        return templates.get(industry, templates["Technology"])
    
    def parse_and_structure_cv(self, cv_text: str, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Parse raw CV text and structure it into our CV format.
        
        Uses pattern matching and AI-like logic to extract:
        - Personal information
        - Work experience
        - Education
        - Skills
        - Awards, projects, etc.
        """
        logger.info(f"Parsing CV text for user {user_id}")
        
        # Initialize structured data
        structured = {
            "personal_info": {
                "surname": "",
                "first_name": "",
                "address": "",
                "phone": "",
                "email": "",
                "nationality": "",
                "date_of_birth": "",
                "gender": "",
            },
            "experience": [],
            "education": [],
            "skills": {
                "mother_tongue": "",
                "other_languages": [],
                "social_skills": [],
                "organizational_skills": [],
                "job_related_skills": [],
                "computer_skills": [],
                "driving_licence": "",
            },
            "awards": [],
            "publications": [],
            "projects": [],
            "memberships": [],
        }
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, cv_text)
        if emails:
            structured["personal_info"]["email"] = emails[0]
        
        # Extract phone
        phone_patterns = [
            r'\+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\+232\s?\d{2}\s?\d{3}\s?\d{4}',  # Sierra Leone format
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, cv_text)
            if phones:
                structured["personal_info"]["phone"] = phones[0]
                break
        
        # Extract name (usually at the top)
        lines = cv_text.split('\n')[:10]
        for line in lines:
            line = line.strip()
            if line and len(line) < 50 and not '@' in line and not any(char.isdigit() for char in line):
                name_parts = line.split()
                if len(name_parts) >= 2:
                    structured["personal_info"]["first_name"] = name_parts[0]
                    structured["personal_info"]["surname"] = " ".join(name_parts[1:])
                    break
        
        # Extract experience (look for common patterns)
        experience_section = self._extract_section(cv_text, ["experience", "work experience", "employment", "career"])
        if experience_section:
            structured["experience"] = self._parse_experience(experience_section)
        
        # Extract education
        education_section = self._extract_section(cv_text, ["education", "qualifications", "academic"])
        if education_section:
            structured["education"] = self._parse_education(education_section)
        
        # Extract skills
        skills_section = self._extract_section(cv_text, ["skills", "competencies", "abilities"])
        if skills_section:
            structured["skills"] = self._parse_skills(skills_section)
        
        # Extract projects
        projects_section = self._extract_section(cv_text, ["projects", "project"])
        if projects_section:
            structured["projects"] = self._parse_list_items(projects_section)
        
        # Extract awards
        awards_section = self._extract_section(cv_text, ["awards", "achievements", "honors"])
        if awards_section:
            structured["awards"] = self._parse_list_items(awards_section)
        
        logger.info(f"Parsed CV: {len(structured['experience'])} experiences, {len(structured['education'])} education entries")
        return structured
    
    def _extract_section(self, text: str, keywords: List[str]) -> Optional[str]:
        """Extract a section from CV text based on keywords."""
        text_lower = text.lower()
        for keyword in keywords:
            pattern = rf'\b{keyword}\b'
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                # Get text from this section to next section or end
                start_idx = match.end()
                # Find next section header (all caps or bold patterns)
                next_section = re.search(r'\n[A-Z][A-Z\s]{3,}\n', text[start_idx:])
                if next_section:
                    return text[start_idx:start_idx + next_section.start()].strip()
                return text[start_idx:].strip()
        return None
    
    def _parse_experience(self, text: str) -> List[Dict[str, Any]]:
        """Parse work experience from text."""
        experiences = []
        # Look for job titles and companies
        lines = text.split('\n')
        current_exp = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this looks like a job title/company line
            if re.match(r'^[A-Z][a-zA-Z\s&]+$', line) and len(line) < 50:
                if current_exp:
                    experiences.append(current_exp)
                current_exp = {
                    "title": line,
                    "company": "",
                    "duration": "",
                    "description": ""
                }
            elif current_exp:
                # Check for date patterns (duration)
                if re.search(r'\d{4}|\d{1,2}[/-]\d{4}', line):
                    current_exp["duration"] = line
                elif not current_exp["company"] and len(line) < 50:
                    current_exp["company"] = line
                else:
                    current_exp["description"] += line + " "
        
        if current_exp:
            experiences.append(current_exp)
        
        return experiences[:10]  # Limit to 10 experiences
    
    def _parse_education(self, text: str) -> List[Dict[str, Any]]:
        """Parse education from text."""
        education = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for degree patterns
            degree_patterns = [r'\b(BSc|BA|MSc|MA|PhD|Bachelor|Master|Doctorate)\b', r'\b(University|College|Institute)\b']
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in degree_patterns):
                education.append({
                    "title": line,
                    "institution": "",
                    "year": ""
                })
        
        return education[:10]
    
    def _parse_skills(self, text: str) -> Dict[str, Any]:
        """Parse skills from text."""
        skills = {
            "job_related_skills": [],
            "computer_skills": [],
            "other_languages": []
        }
        
        # Common skill keywords
        tech_skills = ["python", "javascript", "java", "react", "node", "sql", "html", "css", "git", "docker", "aws", "linux"]
        languages = ["english", "french", "spanish", "arabic", "krio", "temne", "mende"]
        
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        for word in words:
            if word in tech_skills:
                skills["computer_skills"].append(word.title())
            elif word in languages:
                skills["other_languages"].append(word.title())
            elif len(word) > 3:
                skills["job_related_skills"].append(word.title())
        
        # Remove duplicates
        skills["job_related_skills"] = list(set(skills["job_related_skills"]))[:20]
        skills["computer_skills"] = list(set(skills["computer_skills"]))[:15]
        skills["other_languages"] = list(set(skills["other_languages"]))[:10]
        
        return skills
    
    def _parse_list_items(self, text: str) -> List[str]:
        """Parse list items (projects, awards, etc.) from text."""
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Remove bullet points and numbering
            line = re.sub(r'^[•\-\*\d+\.\)]\s*', '', line)
            if line and len(line) > 10:
                items.append(line)
        
        return items[:10]
    
    def tailor_parsed_cv(self, parsed_cv: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Enhance parsed CV with AI improvements.
        - Enhance language in experience descriptions
        - Optimize for ATS
        - Add missing quantifiers
        - Improve formatting
        """
        logger.info("Tailoring parsed CV with AI enhancements")
        
        tailored = parsed_cv.copy()
        
        # Enhance experience descriptions
        for exp in tailored.get("experience", []):
            if exp.get("description"):
                enhanced = self.enhance_language(exp["description"], "experience")
                exp["description"] = enhanced
        
        # Enhance skills formatting
        if tailored.get("skills"):
            # Ensure skills are properly categorized
            all_skills = []
            for category in ["job_related_skills", "computer_skills"]:
                all_skills.extend(tailored["skills"].get(category, []))
            
            # Remove duplicates and standardize
            tailored["skills"]["job_related_skills"] = list(set(all_skills[:15]))
        
        # Add recommendations
        tailored["ai_recommendations"] = self._generate_parsing_recommendations(tailored)
        
        return tailored
    
    def _generate_parsing_recommendations(self, cv_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving the parsed CV."""
        recommendations = []
        
        if not cv_data.get("experience"):
            recommendations.append("Add work experience with quantifiable achievements")
        
        if not cv_data.get("education"):
            recommendations.append("Include your educational qualifications")
        
        if not cv_data.get("skills", {}).get("job_related_skills"):
            recommendations.append("List your key skills and competencies")
        
        # Check for quantifiers in experience
        has_numbers = False
        for exp in cv_data.get("experience", []):
            if re.search(r'\d+', exp.get("description", "")):
                has_numbers = True
                break
        
        if not has_numbers:
            recommendations.append("Add numbers and percentages to quantify your achievements")
        
        return recommendations
