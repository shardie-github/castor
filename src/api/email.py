"""
Email API Routes

Provides endpoints for email management and preferences.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from typing import Optional, List

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.api.auth import get_current_user
from src.email.email_service import EmailService, EmailTemplate

router = APIRouter()


# Pydantic Models
class EmailPreferenceUpdate(BaseModel):
    email_notifications: Optional[bool] = None
    sponsorship_alerts: Optional[bool] = None
    weekly_reports: Optional[bool] = None
    system_updates: Optional[bool] = None


class EmailPreferenceResponse(BaseModel):
    user_id: str
    email_notifications: bool
    sponsorship_alerts: bool
    weekly_reports: bool
    system_updates: bool


def get_postgres_conn(request: Request) -> PostgresConnection:
    """Get PostgreSQL connection from app state"""
    return request.app.state.postgres_conn


def get_email_service(request: Request) -> EmailService:
    """Get email service from app state"""
    if not hasattr(request.app.state, 'email_service'):
        from src.email.email_service import EmailService, EmailProvider
        request.app.state.email_service = EmailService(
            provider=EmailProvider.SENDGRID,
            metrics_collector=request.app.state.metrics_collector,
            event_logger=request.app.state.event_logger
        )
    return request.app.state.email_service


# API Endpoints
@router.get("/email/preferences", response_model=EmailPreferenceResponse)
async def get_email_preferences(
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Get user's email preferences"""
    query = """
        SELECT email_notifications, sponsorship_alerts, weekly_reports, system_updates
        FROM user_email_preferences
        WHERE user_id = $1
    """
    
    result = await postgres_conn.fetchrow(query, current_user['user_id'])
    
    if not result:
        # Return defaults if no preferences set
        return EmailPreferenceResponse(
            user_id=str(current_user['user_id']),
            email_notifications=True,
            sponsorship_alerts=True,
            weekly_reports=False,
            system_updates=True
        )
    
    return EmailPreferenceResponse(
        user_id=str(current_user['user_id']),
        **dict(result)
    )


@router.put("/email/preferences", response_model=EmailPreferenceResponse)
async def update_email_preferences(
    preferences: EmailPreferenceUpdate,
    current_user: dict = Depends(get_current_user),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """Update user's email preferences"""
    # Upsert preferences
    query = """
        INSERT INTO user_email_preferences (
            user_id, email_notifications, sponsorship_alerts,
            weekly_reports, system_updates
        )
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (user_id) DO UPDATE SET
            email_notifications = COALESCE(EXCLUDED.email_notifications, user_email_preferences.email_notifications),
            sponsorship_alerts = COALESCE(EXCLUDED.sponsorship_alerts, user_email_preferences.sponsorship_alerts),
            weekly_reports = COALESCE(EXCLUDED.weekly_reports, user_email_preferences.weekly_reports),
            system_updates = COALESCE(EXCLUDED.system_updates, user_email_preferences.system_updates),
            updated_at = NOW()
        RETURNING user_id, email_notifications, sponsorship_alerts, weekly_reports, system_updates
    """
    
    result = await postgres_conn.fetchrow(
        query,
        current_user['user_id'],
        preferences.email_notifications,
        preferences.sponsorship_alerts,
        preferences.weekly_reports,
        preferences.system_updates
    )
    
    return EmailPreferenceResponse(**dict(result))


@router.post("/email/test")
async def send_test_email(
    current_user: dict = Depends(get_current_user),
    email_service: EmailService = Depends(get_email_service)
):
    """Send a test email to the current user"""
    # Get user email
    from src.database import PostgresConnection
    postgres_conn = email_service.postgres_conn if hasattr(email_service, 'postgres_conn') else None
    
    if not postgres_conn:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available"
        )
    
    user = await postgres_conn.fetchrow(
        "SELECT email, name FROM users WHERE user_id = $1",
        current_user['user_id']
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    success = await email_service.send_email(
        to_email=user['email'],
        template=EmailTemplate.WELCOME,
        context={'name': user['name']}
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test email"
        )
    
    return {"message": "Test email sent successfully"}
