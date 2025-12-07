from typing import Dict, Any
from sqlalchemy.orm import Session
from app.db.models import Startup, Investment, User
from app.utils.logger import logger


class CredibilityService:
    """Service for calculating startup credibility scores."""
    
    def calculate_startup_credibility(
        self,
        db: Session,
        startup_id: int
    ) -> Dict[str, Any]:
        """
        Calculate credibility score for a startup based on:
        - Verified employee certificates
        - Founder certificate
        - Investment traction
        - On-chain legitimacy
        """
        logger.info(f"Calculating credibility for startup {startup_id}")
        
        startup = db.query(Startup).filter(Startup.id == startup_id).first()
        if not startup:
            return {"credibility_score": 0.0, "factors": {}}
        
        factors = {}
        score = 0.0
        
        # Factor 1: Verified employees (40 points max)
        employees_verified = startup.employees_verified or 0
        employee_score = min(40, employees_verified * 8)  # 8 points per verified employee
        factors["verified_employees"] = {
            "count": employees_verified,
            "score": employee_score
        }
        score += employee_score
        
        # Factor 2: Founder verification (20 points) - Certificates removed, using on-chain verification
        founder = db.query(User).filter(User.id == startup.founder_id).first()
        founder_score = 20 if (founder and founder.verified_on_chain == "verified") else 0
        factors["founder_verification"] = {
            "verified": founder_score > 0,
            "score": founder_score
        }
        score += founder_score
        
        # Factor 3: Investment traction (30 points max)
        investments = db.query(Investment).filter(
            Investment.startup_id == startup_id
        ).all()
        total_investment = sum(inv.amount for inv in investments)
        investment_score = min(30, (total_investment / 10000) * 30)  # Scale based on 10k USDC
        factors["investment_traction"] = {
            "total_investments": len(investments),
            "total_amount": total_investment,
            "score": investment_score
        }
        score += investment_score
        
        # Factor 4: On-chain legitimacy (10 points)
        on_chain_score = 10 if startup.transaction_signature else 0
        factors["on_chain_legitimacy"] = {
            "registered_on_chain": startup.transaction_signature is not None,
            "score": on_chain_score
        }
        score += on_chain_score
        
        # Update startup credibility score
        startup.credibility_score = round(score, 2)
        db.commit()
        
        logger.info(f"Startup {startup_id} credibility score: {score}")
        
        return {
            "credibility_score": round(score, 2),
            "factors": factors,
            "grade": self._get_credibility_grade(score)
        }
    
    def _get_credibility_grade(self, score: float) -> str:
        """Get credibility grade based on score."""
        if score >= 80:
            return "A+"
        elif score >= 70:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C"
        elif score >= 40:
            return "D"
        else:
            return "F"

