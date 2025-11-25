"""
Referrals API

Handles referral code generation, tracking, and rewards.
"""

import logging
import secrets
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.database import PostgresConnection

logger = logging.getLogger(__name__)

router = APIRouter()


# Dependencies
async def get_postgres_conn() -> PostgresConnection:
    """Get PostgreSQL connection from app state"""
    from src.main import app
    return app.state.postgres_conn


# Request/Response Models
class ReferralCodeResponse(BaseModel):
    """Referral code response"""
    code: str
    referral_url: str
    total_referrals: int
    completed_referrals: int


class CreateReferralRequest(BaseModel):
    """Create referral request"""
    referrer_id: str


class UseReferralRequest(BaseModel):
    """Use referral request"""
    code: str
    referred_id: str


@router.post("/referrals", response_model=ReferralCodeResponse)
async def create_referral_code(
    request: CreateReferralRequest,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """
    Create a referral code for a user
    """
    try:
        # Generate unique referral code
        code = secrets.token_urlsafe(8).upper()[:8]  # 8-character code
        
        # Check if code already exists
        check_query = "SELECT id FROM referrals WHERE code = $1"
        existing = await postgres_conn.fetch_one(check_query, code)
        
        if existing:
            # Regenerate if collision (unlikely)
            code = secrets.token_urlsafe(8).upper()[:8]
        
        # Insert referral code
        insert_query = """
            INSERT INTO referrals (referrer_id, code, status)
            VALUES ($1::uuid, $2, 'pending')
            RETURNING id
        """
        
        await postgres_conn.execute(insert_query, request.referrer_id, code)
        
        # Get referral stats
        stats_query = """
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'completed') as completed
            FROM referrals
            WHERE referrer_id = $1::uuid
        """
        stats = await postgres_conn.fetch_one(stats_query, request.referrer_id)
        
        # Build referral URL (would use actual domain in production)
        referral_url = f"https://yourapp.com/signup?ref={code}"
        
        return ReferralCodeResponse(
            code=code,
            referral_url=referral_url,
            total_referrals=stats["total"] or 0 if stats else 0,
            completed_referrals=stats["completed"] or 0 if stats else 0
        )
    except Exception as e:
        logger.error(f"Error creating referral code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/referrals/use")
async def use_referral_code(
    request: UseReferralRequest,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """
    Use a referral code during signup
    """
    try:
        # Find referral code
        find_query = """
            SELECT id, referrer_id, status
            FROM referrals
            WHERE code = $1
        """
        referral = await postgres_conn.fetch_one(find_query, request.code)
        
        if not referral:
            raise HTTPException(status_code=404, detail="Referral code not found")
        
        if referral["status"] == "completed":
            raise HTTPException(status_code=400, detail="Referral code already used")
        
        # Update referral
        update_query = """
            UPDATE referrals
            SET referred_id = $1::uuid,
                status = 'completed',
                completed_at = NOW()
            WHERE id = $2::uuid
        """
        
        await postgres_conn.execute(
            update_query,
            request.referred_id,
            referral["id"]
        )
        
        # Apply rewards (would integrate with billing system)
        # For now, just log the reward
        logger.info(f"Referral completed: {request.code} by {request.referred_id}")
        
        return {
            "success": True,
            "message": "Referral code applied successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error using referral code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/referrals/{user_id}", response_model=ReferralCodeResponse)
async def get_referral_code(
    user_id: str,
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """
    Get referral code for a user (or create if doesn't exist)
    """
    try:
        # Check if user has referral code
        find_query = """
            SELECT code
            FROM referrals
            WHERE referrer_id = $1::uuid
            ORDER BY created_at DESC
            LIMIT 1
        """
        existing = await postgres_conn.fetch_one(find_query, user_id)
        
        if existing:
            code = existing["code"]
        else:
            # Create new referral code
            create_request = CreateReferralRequest(referrer_id=user_id)
            response = await create_referral_code(create_request, postgres_conn)
            return response
        
        # Get stats
        stats_query = """
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'completed') as completed
            FROM referrals
            WHERE referrer_id = $1::uuid
        """
        stats = await postgres_conn.fetch_one(stats_query, user_id)
        
        referral_url = f"https://yourapp.com/signup?ref={code}"
        
        return ReferralCodeResponse(
            code=code,
            referral_url=referral_url,
            total_referrals=stats["total"] or 0 if stats else 0,
            completed_referrals=stats["completed"] or 0 if stats else 0
        )
    except Exception as e:
        logger.error(f"Error getting referral code: {e}")
        raise HTTPException(status_code=500, detail=str(e))
