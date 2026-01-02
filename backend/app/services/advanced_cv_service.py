"""
Advanced CV Service with comprehensive AI features
Includes guided CV creation, job matching, cover letters, ATS optimization, and more
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.utils.logger import logger
from app.core.config import settings
import json
import re
from datetime import datetime


class AdvancedCVService:
    """Advanced CV service with AI-powered features."""
    
    def __init__(self):
        self.mistral_key = settings.MISTRAL_API_KEY or settings.OPENAI_API_KEY  # Backward compatibility
    
    def generate_cv_from_questions(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate CV from guided questionnaire answers.
        
        Args:
            answers: Dictionary with user responses to guided questions
            
        Returns:
            Generated CV in structured format
        """
        logger.info("Generating CV from questionnaire answers")
        
        if not self.mistral_key:
            return self._generate_cv_fallback(answers)
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            prompt = self._build_cv_generation_prompt(answers)
            
            response = client.chat.complete(
                model="mistral-medium-latest",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert CV writer and ATS optimization specialist. 
                        Generate a professional, ATS-friendly CV in JSON format. 
                        Include quantifiable achievements, action verbs, and industry keywords.
                        Format: {
                            "summary": "professional summary",
                            "personal_info": {...},
                            "experience": [...],
                            "education": [...],
                            "skills": {...},
                            "achievements": [...],
                            "certifications": [...]
                        }"""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content.strip()
            # Extract JSON from response
            cv_data = self._extract_json(content)
            
            return {
                "success": True,
                "cv_data": cv_data,
                "text_version": self._format_cv_text(cv_data),
                "ats_score": self._calculate_ats_score(cv_data)
            }
            
        except Exception as e:
            logger.error(f"Error generating CV: {e}")
            return self._generate_cv_fallback(answers)
    
    def match_job_compatibility(self, cv_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """
        Compute compatibility score between CV and job description.
        
        Returns:
            Compatibility analysis with score, missing skills, recommendations
        """
        logger.info("Computing job compatibility")
        
        if not self.mistral_key:
            return self._match_job_fallback(cv_data, job_description)
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            cv_summary = json.dumps(cv_data, indent=2)
            
            prompt = f"""Analyze the compatibility between this CV and job description.

CV Data:
{cv_summary}

Job Description:
{job_description}

Provide analysis in JSON format:
{{
    "compatibility_score": 0-100,
    "matched_skills": ["skill1", "skill2"],
    "missing_skills": ["skill1", "skill2"],
    "matched_experience": "years of relevant experience",
    "missing_qualifications": ["qualification1"],
    "recommendations": [
        "specific bullet point to add",
        "skill to highlight",
        "experience to emphasize"
    ],
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"]
}}"""
            
            response = client.chat.complete(
                model="mistral-medium-latest",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a recruitment expert. Analyze CV-job compatibility objectively."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            analysis = self._extract_json(content)
            
            return {
                "success": True,
                "analysis": analysis,
                "score": analysis.get("compatibility_score", 0)
            }
            
        except Exception as e:
            logger.error(f"Error matching job: {e}")
            return self._match_job_fallback(cv_data, job_description)
    
    def generate_job_optimized_cv(self, cv_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """Generate a job-optimized version of the CV"""
        logger.info("Generating job-optimized CV")
        
        compatibility = self.match_job_compatibility(cv_data, job_description)
        recommendations = compatibility.get("analysis", {}).get("recommendations", [])
        
        if not self.mistral_key:
            return {"success": False, "message": "Mistral AI API key not configured"}
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            prompt = f"""Optimize this CV for the specific job description.

Original CV:
{json.dumps(cv_data, indent=2)}

Job Description:
{job_description}

Optimization Recommendations:
{json.dumps(recommendations, indent=2)}

Create an optimized version that:
1. Incorporates missing keywords from job description
2. Highlights relevant experience more prominently
3. Adds recommended skills/qualifications
4. Rewrites bullets to match job requirements
5. Maintains authenticity and truthfulness

Return optimized CV in same JSON format."""
            
            response = client.chat.complete(
                model="mistral-medium-latest",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a CV optimization expert. Create job-tailored CVs that are truthful and effective."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content.strip()
            optimized_cv = self._extract_json(content)
            
            return {
                "success": True,
                "optimized_cv": optimized_cv,
                "changes_made": recommendations,
                "original_score": compatibility.get("score", 0)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing CV: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_cover_letter(self, cv_data: Dict[str, Any], job_description: str, company_name: str = "") -> Dict[str, Any]:
        """Generate personalized cover letter"""
        logger.info("Generating cover letter")
        
        if not self.mistral_key:
            return {"success": False, "message": "Mistral AI API key not configured"}
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            prompt = f"""Write a professional, personalized cover letter.

CV Information:
{json.dumps(cv_data, indent=2)}

Job Description:
{job_description}

Company: {company_name}

Requirements:
1. Professional tone, 3-4 paragraphs
2. Highlight relevant experience from CV
3. Show enthusiasm for the role
4. Connect skills to job requirements
5. Include specific examples
6. Professional closing

Generate the cover letter text."""
            
            response = client.chat.complete(
                model="mistral-medium-latest",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional cover letter writer. Create compelling, personalized cover letters."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            cover_letter = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "cover_letter": cover_letter,
                "word_count": len(cover_letter.split())
            }
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return {"success": False, "error": str(e)}
    
    def extract_skills_from_cv(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and categorize skills from CV"""
        skills = {
            "hard_skills": [],
            "soft_skills": [],
            "tools": [],
            "languages": [],
            "certifications": []
        }
        
        # Extract from skills section
        if "skills" in cv_data:
            skills_data = cv_data["skills"]
            skills["hard_skills"].extend(skills_data.get("technical", []))
            skills["soft_skills"].extend(skills_data.get("soft", []))
            skills["tools"].extend(skills_data.get("tools", []))
            skills["languages"].extend(skills_data.get("languages", []))
        
        # Extract from experience
        if "experience" in cv_data:
            for exp in cv_data["experience"]:
                description = exp.get("description", "").lower()
                # Simple keyword extraction
                tech_keywords = ["python", "javascript", "react", "node", "sql", "aws", "docker"]
                for keyword in tech_keywords:
                    if keyword in description and keyword not in skills["hard_skills"]:
                        skills["hard_skills"].append(keyword)
        
        return skills
    
    def generate_interview_questions(self, cv_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """Generate interview questions based on CV and job description"""
        logger.info("Generating interview questions")
        
        if not self.mistral_key:
            return {"success": False, "message": "Mistral AI API key not configured"}
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            prompt = f"""Generate interview questions for this candidate and role.

CV:
{json.dumps(cv_data, indent=2)}

Job Description:
{job_description}

Generate:
1. 5 behavioral questions (STAR method)
2. 5 technical questions (if applicable)
3. 3 situational questions
4. Model answers for each

Format as JSON:
{{
    "behavioral": [
        {{"question": "...", "model_answer": "...", "key_points": [...]}}
    ],
    "technical": [...],
    "situational": [...]
}}"""
            
            response = client.chat.complete(
                model="mistral-medium-latest",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an interview preparation expert. Generate relevant questions and model answers."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            questions = self._extract_json(content)
            
            return {
                "success": True,
                "questions": questions
            }
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return {"success": False, "error": str(e)}
    
    def optimize_ats(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive ATS optimization analysis"""
        score = 0
        issues = []
        suggestions = []
        
        # Check formatting
        if not cv_data.get("summary"):
            issues.append("Missing professional summary")
            score -= 10
        else:
            score += 10
        
        # Check keywords
        cv_text = json.dumps(cv_data).lower()
        common_keywords = ["experience", "skills", "education", "achievement"]
        keyword_count = sum(1 for kw in common_keywords if kw in cv_text)
        score += min(keyword_count * 5, 20)
        
        # Check quantifiable achievements
        experience = cv_data.get("experience", [])
        has_metrics = False
        for exp in experience:
            desc = exp.get("description", "").lower()
            if any(char.isdigit() for char in desc):
                has_metrics = True
                break
        
        if has_metrics:
            score += 15
        else:
            issues.append("Missing quantifiable achievements")
            suggestions.append("Add numbers, percentages, or metrics to experience descriptions")
        
        # Check structure
        required_sections = ["personal_info", "experience", "education", "skills"]
        missing_sections = [s for s in required_sections if s not in cv_data]
        if missing_sections:
            issues.append(f"Missing sections: {', '.join(missing_sections)}")
            score -= len(missing_sections) * 10
        
        # Final score (0-100)
        score = max(0, min(100, score))
        
        return {
            "ats_score": score,
            "issues": issues,
            "suggestions": suggestions,
            "grade": self._get_ats_grade(score)
        }
    
    def generate_career_recommendations(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate career path recommendations"""
        skills = self.extract_skills_from_cv(cv_data)
        
        # Simple career mapping (can be enhanced with LLM)
        career_paths = []
        
        if any("python" in s.lower() or "javascript" in s.lower() for s in skills["hard_skills"]):
            career_paths.append({
                "title": "Software Developer",
                "match_score": 85,
                "required_skills": ["Python", "JavaScript", "Git"],
                "salary_range": "$60k - $120k",
                "next_steps": ["Learn React", "Build portfolio projects", "Get certifications"]
            })
        
        return {
            "career_paths": career_paths,
            "skill_gaps": [],
            "learning_resources": []
        }
    
    # Helper methods
    def _build_cv_generation_prompt(self, answers: Dict[str, Any]) -> str:
        """Build prompt for CV generation from questionnaire"""
        prompt = f"""Create a professional CV based on these answers:

Role/Industry: {answers.get('role', 'Not specified')}
Experience Level: {answers.get('experience_level', 'Not specified')}
Years of Experience: {answers.get('years_experience', 'Not specified')}
Key Achievements: {answers.get('achievements', 'None')}
Skills: {', '.join(answers.get('skills', []))}
Education: {answers.get('education', 'Not specified')}
Location: {answers.get('location', 'Not specified')}
Desired Salary: {answers.get('desired_salary', 'Not specified')}
Portfolio Links: {answers.get('portfolio_links', 'None')}

Generate a complete, ATS-optimized CV in JSON format."""
        return prompt
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response"""
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # Fallback: try parsing entire text
        try:
            return json.loads(text)
        except:
            return {"error": "Could not parse JSON response"}
    
    def _format_cv_text(self, cv_data: Dict[str, Any]) -> str:
        """Format CV data as readable text"""
        lines = []
        
        # Personal Info
        if "personal_info" in cv_data:
            info = cv_data["personal_info"]
            lines.append(f"{info.get('full_name', '')}")
            lines.append(f"{info.get('email', '')} | {info.get('phone', '')}")
            lines.append("")
        
        # Summary
        if "summary" in cv_data:
            lines.append("PROFESSIONAL SUMMARY")
            lines.append(cv_data["summary"])
            lines.append("")
        
        # Experience
        if "experience" in cv_data:
            lines.append("EXPERIENCE")
            for exp in cv_data["experience"]:
                lines.append(f"{exp.get('job_title', '')} at {exp.get('company', '')}")
                lines.append(exp.get("description", ""))
                lines.append("")
        
        return "\n".join(lines)
    
    def _calculate_ats_score(self, cv_data: Dict[str, Any]) -> int:
        """Calculate basic ATS score"""
        return self.optimize_ats(cv_data)["ats_score"]
    
    def _get_ats_grade(self, score: int) -> str:
        """Get letter grade for ATS score"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        else:
            return "D"
    
    def _generate_cv_fallback(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback CV generation without OpenAI"""
        return {
            "success": True,
            "cv_data": {
                "summary": f"Experienced {answers.get('role', 'professional')}",
                "personal_info": {
                    "full_name": answers.get("full_name", ""),
                    "email": answers.get("email", ""),
                    "location": answers.get("location", "")
                },
                "experience": [],
                "education": [],
                "skills": {"technical": answers.get("skills", [])}
            },
            "text_version": "Basic CV generated",
            "ats_score": 60
        }
    
    def get_field_suggestions(self, field: str, current_value: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get 10+ AI suggestions for a specific CV field.
        
        Args:
            field: Field name (e.g., "summary", "experience.0.description")
            current_value: Current value user has typed
            context: Additional context (step, section, etc.)
            
        Returns:
            List of 10+ suggestions
        """
        logger.info(f"Getting suggestions for field: {field}")
        
        if not self.mistral_key:
            return {
                "success": False,
                "suggestions": self._get_fallback_suggestions(field, current_value)
            }
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            # Build context-aware prompt
            context_str = ""
            if context:
                if context.get("job_title"):
                    context_str += f"Job Title: {context['job_title']}\n"
                if context.get("company"):
                    context_str += f"Company: {context['company']}\n"
                if context.get("experience"):
                    context_str += f"Years of Experience: {context['experience']}\n"
            
            # Handle empty values for proactive suggestions
            value_context = f"Current Value: {current_value}" if current_value else "Field is currently empty - provide initial suggestions"
            is_proactive = context.get("proactive", False) or not current_value
            
            prompt = f"""You are an expert CV writer. Provide 15+ professional suggestions for this CV field.

Field: {field}
{value_context}
Context: {context_str}
{"Note: This is a proactive suggestion request - provide initial examples to help the user get started." if is_proactive else ""}

Requirements:
1. Provide at least 15 different suggestions
2. Each suggestion should be a complete, professional statement
3. Use action verbs and quantifiable metrics
4. Make suggestions ATS-friendly
5. Vary the style and approach
6. Be specific and industry-relevant
{"7. Since the field is empty, provide diverse examples covering different experience levels and industries" if is_proactive else ""}

Return ONLY a JSON array of strings, no other text:
["suggestion 1", "suggestion 2", "suggestion 3", ...]"""
            
            response = client.chat.complete(
                model="mistral-medium-latest",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional CV writing expert. Provide 15+ high-quality suggestions in JSON array format only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON array
            import json
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group())
                # Ensure we have at least 10 suggestions
                if len(suggestions) < 10:
                    suggestions.extend(self._get_fallback_suggestions(field, current_value)[len(suggestions):])
                
                return {
                    "success": True,
                    "suggestions": suggestions[:20]  # Return up to 20
                }
            else:
                # Fallback if JSON parsing fails
                return {
                    "success": True,
                    "suggestions": self._get_fallback_suggestions(field, current_value)
                }
                
        except Exception as e:
            logger.error(f"Error getting field suggestions: {e}")
            return {
                "success": True,
                "suggestions": self._get_fallback_suggestions(field, current_value)
            }
    
    def _get_fallback_suggestions(self, field: str, current_value: str) -> List[str]:
        """Fallback suggestions when OpenAI is not available"""
        suggestions = []
        
        if "summary" in field.lower():
            suggestions = [
                f"Results-driven {current_value[:20]}... professional with proven track record",
                f"Experienced {current_value[:20]}... specializing in delivering measurable results",
                f"Dynamic {current_value[:20]}... expert with {len(current_value)} years of experience",
                f"Strategic {current_value[:20]}... professional known for driving innovation",
                f"Accomplished {current_value[:20]}... with expertise in multiple domains",
            ]
        elif "experience" in field.lower() or "description" in field.lower():
            suggestions = [
                f"Led cross-functional teams to achieve {current_value[:15]}... resulting in 30% improvement",
                f"Developed and implemented {current_value[:15]}... strategies that increased efficiency by 25%",
                f"Managed {current_value[:15]}... projects with budgets exceeding $500K",
                f"Collaborated with stakeholders to deliver {current_value[:15]}... solutions",
                f"Optimized {current_value[:15]}... processes reducing costs by 20%",
            ]
        
        # Add more generic suggestions to reach 10+
        while len(suggestions) < 15:
            suggestions.append(f"Enhanced {current_value[:20]}... through strategic initiatives")
        
        return suggestions[:15]
    
    def _match_job_fallback(self, cv_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """Fallback job matching without OpenAI"""
        # Simple keyword matching
        cv_text = json.dumps(cv_data).lower()
        job_lower = job_description.lower()
        
        # Count matching keywords
        job_words = set(re.findall(r'\b\w{4,}\b', job_lower))
        cv_words = set(re.findall(r'\b\w{4,}\b', cv_text))
        matches = job_words.intersection(cv_words)
        
        score = min(100, len(matches) * 5)
        
        return {
            "success": True,
            "analysis": {
                "compatibility_score": score,
                "matched_skills": list(matches)[:10],
                "missing_skills": [],
                "recommendations": ["Add more relevant keywords from job description"]
            },
            "score": score
        }

