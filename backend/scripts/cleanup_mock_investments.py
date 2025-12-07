#!/usr/bin/env python3
"""
Cleanup script to remove mock investments from the database.
Real investments should only be created through the UI with proper blockchain transactions.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Investment
from app.utils.logger import logger

def cleanup_mock_investments():
    """Remove all investments with mock transaction signatures."""
    db: Session = SessionLocal()
    
    try:
        print("🧹 Cleaning up mock investments...")
        
        # Find all investments with mock transaction signatures
        mock_investments = db.query(Investment).filter(
            Investment.tx_signature.like("mock_%")
        ).all()
        
        if not mock_investments:
            print("✅ No mock investments found. Database is clean!")
            return
        
        print(f"Found {len(mock_investments)} mock investment(s) to remove:")
        for inv in mock_investments:
            print(f"  - Investment ID {inv.id}: {inv.amount} USDC (tx: {inv.tx_signature})")
        
        # Delete mock investments
        for inv in mock_investments:
            db.delete(inv)
        
        db.commit()
        print(f"✅ Removed {len(mock_investments)} mock investment(s)")
        print("\n💡 Note: Real investments should be made through the UI, which will create proper blockchain transactions.")
        
    except Exception as e:
        print(f"❌ Error cleaning up mock investments: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    cleanup_mock_investments()

