"""
PDF Parser Service for LinkedIn CV Upload
Extracts text from PDF and uses Mistral AI to parse structured CV data
"""
from typing import Dict, Any, Optional
import io
import re
from fastapi import UploadFile
from app.utils.logger import logger
from app.core.config import settings

try:
    import PyPDF2
    import pdfplumber
except ImportError:
    logger.warning("PDF libraries not installed. PDF upload feature will not work.")
    PyPDF2 = None
    pdfplumber = None


class PDFParserService:
    """Service for parsing LinkedIn CV PDFs using AI"""
    
    def __init__(self):
        self.mistral_key = settings.MISTRAL_API_KEY
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    async def extract_text_from_pdf(self, file: UploadFile) -> str:
        """
        Extract text from PDF file using multiple methods for best results.
        
        Args:
            file: Uploaded PDF file
            
        Returns:
            Extracted text content
        """
        try:
            # Read file content
            content = await file.read()
            
            # Try pdfplumber first (better for formatted PDFs like LinkedIn)
            if pdfplumber:
                try:
                    pdf_file = io.BytesIO(content)
                    text = ""
                    with pdfplumber.open(pdf_file) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                    
                    if text.strip():
                        logger.info(f"Extracted {len(text)} characters using pdfplumber")
                        return text.strip()
                except Exception as e:
                    logger.warning(f"pdfplumber extraction failed: {e}")
            
            # Fallback to PyPDF2
            if PyPDF2:
                try:
                    pdf_file = io.BytesIO(content)
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text = ""
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    
                    if text.strip():
                        logger.info(f"Extracted {len(text)} characters using PyPDF2")
                        return text.strip()
                except Exception as e:
                    logger.error(f"PyPDF2 extraction failed: {e}")
            
            raise Exception("Could not extract text from PDF")
            
        except Exception as e:
            logger.error(f"PDF text extraction error: {e}")
            raise
    
    async def parse_linkedin_cv(self, pdf_text: str) -> Dict[str, Any]:
        """
        Use Mistral AI to parse LinkedIn CV text into structured data.
        
        Args:
            pdf_text: Raw text extracted from PDF
            
        Returns:
            Structured CV data
        """
        if not self.mistral_key:
            logger.warning("Mistral API key not configured, using fallback parser")
            return self._fallback_parse(pdf_text)
        
        try:
            from mistralai import Mistral
            client = Mistral(api_key=self.mistral_key)
            
            prompt = f"""You are an expert CV parser. Extract structured information from this LinkedIn CV text.

CV Text:
{pdf_text[:8000]}

Return ONLY valid JSON in this exact format (no markdown, no code blocks):
{{
  "personal_info": {{
    "first_name": "",
    "surname": "",
    "email": "",
    "phone": "",
    "address": "",
    "linkedin": "",
    "nationality": ""
  }},
  "summary": "",
  "experience": [
    {{
      "job_title": "",
      "company": "",
      "location": "",
      "start_date": "",
      "end_date": "",
      "description": ""
    }}
  ],
  "education": [
    {{
      "degree": "",
      "institution": "",
      "field_of_study": "",
      "start_date": "",
      "end_date": "",
      "grade": ""
    }}
  ],
  "skills": {{
    "technical": [],
    "soft": [],
    "languages": []
  }},
  "certifications": [
    {{
      "name": "",
      "issuer": "",
      "date": ""
    }}
  ],
  "projects": [],
  "awards": []
}}

Extract all available information. Use empty strings or arrays if information is not found."""
            
            response = client.chat.complete(
                model="mistral-medium-latest",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a CV parsing expert. Extract structured data and return ONLY valid JSON, no markdown formatting."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent parsing
                max_tokens=4000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            import json
            cv_data = json.loads(content)
            
            logger.info("Successfully parsed CV with Mistral AI")
            return cv_data
            
        except Exception as e:
            logger.error(f"Mistral AI parsing error: {e}, using fallback")
            return self._fallback_parse(pdf_text)
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """
        Fallback parser using regex and heuristics when AI is not available.
        
        Args:
            text: Raw CV text
            
        Returns:
            Basic structured CV data
        """
        logger.info("Using fallback parser")
        
        cv_data = {
            "personal_info": {},
            "summary": "",
            "experience": [],
            "education": [],
            "skills": {"technical": [], "soft": [], "languages": []},
            "certifications": [],
            "projects": [],
            "awards": []
        }
        
        # Extract email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            cv_data["personal_info"]["email"] = email_match.group()
        
        # Extract phone
        phone_match = re.search(r'\+?[\d\s\-\(\)]{10,}', text)
        if phone_match:
            cv_data["personal_info"]["phone"] = phone_match.group().strip()
        
        # Extract LinkedIn URL
        linkedin_match = re.search(r'linkedin\.com/in/[\w\-]+', text)
        if linkedin_match:
            cv_data["personal_info"]["linkedin"] = linkedin_match.group()
        
        # Try to extract name (first line often contains name)
        lines = text.split('\n')
        if lines:
            first_line = lines[0].strip()
            if len(first_line.split()) <= 4 and len(first_line) < 50:
                name_parts = first_line.split()
                if len(name_parts) >= 2:
                    cv_data["personal_info"]["first_name"] = name_parts[0]
                    cv_data["personal_info"]["surname"] = " ".join(name_parts[1:])
        
        # Extract summary (look for common summary keywords)
        summary_keywords = ["summary", "profile", "about", "objective"]
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in summary_keywords):
                # Get next few lines as summary
                summary_lines = []
                for j in range(i+1, min(i+6, len(lines))):
                    if lines[j].strip() and not any(k in lines[j].lower() for k in ["experience", "education", "skills"]):
                        summary_lines.append(lines[j].strip())
                cv_data["summary"] = " ".join(summary_lines)
                break
        
        return cv_data
    
    def validate_cv_data(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean extracted CV data.
        
        Args:
            cv_data: Extracted CV data
            
        Returns:
            Validated and cleaned CV data
        """
        # Ensure required fields exist
        if "personal_info" not in cv_data:
            cv_data["personal_info"] = {}
        
        if "experience" not in cv_data:
            cv_data["experience"] = []
        
        if "education" not in cv_data:
            cv_data["education"] = []
        
        if "skills" not in cv_data:
            cv_data["skills"] = {"technical": [], "soft": [], "languages": []}
        
        # Clean email
        if cv_data["personal_info"].get("email"):
            email = cv_data["personal_info"]["email"].strip().lower()
            if "@" in email:
                cv_data["personal_info"]["email"] = email
        
        # Clean phone
        if cv_data["personal_info"].get("phone"):
            phone = re.sub(r'[^\d\+\-\(\)\s]', '', cv_data["personal_info"]["phone"])
            cv_data["personal_info"]["phone"] = phone.strip()
        
        return cv_data
