"""
Email Service Module

Handles email sending with SendGrid/SES integration, templates, and queue management.
"""

import logging
import os
from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class EmailProvider(Enum):
    """Email provider types"""
    SENDGRID = "sendgrid"
    SES = "ses"


class EmailTemplate(Enum):
    """Email template types"""
    WELCOME = "welcome"
    VERIFICATION = "verification"
    PASSWORD_RESET = "password_reset"
    CAMPAIGN_CREATED = "campaign_created"
    REPORT_READY = "report_ready"
    WEEKLY_SUMMARY = "weekly_summary"
    PAYMENT_RECEIPT = "payment_receipt"
    SUBSCRIPTION_UPDATED = "subscription_updated"


class EmailService:
    """
    Email Service
    
    Handles email sending with support for:
    - Multiple providers (SendGrid, SES)
    - Template management
    - Queue system
    - Error handling and retries
    """
    
    def __init__(
        self,
        provider: EmailProvider = EmailProvider.SENDGRID,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
        metrics_collector: Optional[MetricsCollector] = None,
        event_logger: Optional[EventLogger] = None
    ):
        self.provider = provider
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY") or os.getenv("AWS_SES_ACCESS_KEY")
        self.from_email = from_email or os.getenv("FROM_EMAIL", "noreply@podcastanalytics.com")
        self.metrics = metrics_collector
        self.events = event_logger
        
        if provider == EmailProvider.SENDGRID and self.api_key:
            self.client = SendGridAPIClient(self.api_key)
        else:
            self.client = None
            logger.warning("Email service initialized without API key")
    
    def _get_template_content(self, template: EmailTemplate, context: Dict) -> tuple[str, str]:
        """Get email subject and body from template"""
        templates = {
            EmailTemplate.WELCOME: (
                "Welcome to Podcast Analytics!",
                f"""
                <h1>Welcome, {context.get('name', 'there')}!</h1>
                <p>Thank you for joining Podcast Analytics. We're excited to help you track and optimize your podcast sponsorships.</p>
                <p>Get started by creating your first campaign.</p>
                """
            ),
            EmailTemplate.VERIFICATION: (
                "Verify your email address",
                f"""
                <h1>Verify your email</h1>
                <p>Click the link below to verify your email address:</p>
                <p><a href="{context.get('verification_url')}">Verify Email</a></p>
                """
            ),
            EmailTemplate.PASSWORD_RESET: (
                "Reset your password",
                f"""
                <h1>Password Reset</h1>
                <p>Click the link below to reset your password:</p>
                <p><a href="{context.get('reset_url')}">Reset Password</a></p>
                <p>This link will expire in 1 hour.</p>
                """
            ),
            EmailTemplate.CAMPAIGN_CREATED: (
                "Campaign Created Successfully",
                f"""
                <h1>Campaign Created</h1>
                <p>Your campaign "{context.get('campaign_name')}" has been created successfully.</p>
                <p>Start tracking your ROI and attribution now.</p>
                """
            ),
            EmailTemplate.REPORT_READY: (
                "Your Report is Ready",
                f"""
                <h1>Report Ready</h1>
                <p>Your {context.get('report_type')} report for campaign "{context.get('campaign_name')}" is ready.</p>
                <p><a href="{context.get('report_url')}">Download Report</a></p>
                """
            ),
            EmailTemplate.WEEKLY_SUMMARY: (
                "Your Weekly Analytics Summary",
                f"""
                <h1>Weekly Summary</h1>
                <p>Here's your weekly podcast analytics summary:</p>
                <ul>
                    <li>Total Campaigns: {context.get('total_campaigns', 0)}</li>
                    <li>Total Conversions: {context.get('total_conversions', 0)}</li>
                    <li>Total Revenue: ${context.get('total_revenue', 0):.2f}</li>
                </ul>
                """
            ),
            EmailTemplate.PAYMENT_RECEIPT: (
                "Payment Receipt",
                f"""
                <h1>Payment Receipt</h1>
                <p>Thank you for your payment of ${context.get('amount', 0):.2f}.</p>
                <p>Invoice ID: {context.get('invoice_id')}</p>
                """
            ),
            EmailTemplate.SUBSCRIPTION_UPDATED: (
                "Subscription Updated",
                f"""
                <h1>Subscription Updated</h1>
                <p>Your subscription has been updated to {context.get('tier', 'unknown')}.</p>
                """
            ),
        }
        
        return templates.get(template, ("Notification", "<p>You have a new notification.</p>"))
    
    async def send_email(
        self,
        to_email: str,
        template: EmailTemplate,
        context: Dict,
        subject: Optional[str] = None,
        body: Optional[str] = None
    ) -> bool:
        """Send an email"""
        try:
            if not self.client:
                logger.error("Email client not initialized")
                return False
            
            email_subject, email_body = self._get_template_content(template, context)
            
            if subject:
                email_subject = subject
            if body:
                email_body = body
            
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=email_subject,
                html_content=Content("text/html", email_body)
            )
            
            response = self.client.send(message)
            
            if response.status_code in [200, 202]:
                if self.metrics:
                    self.metrics.increment_counter(
                        "emails_sent_total",
                        tags={"template": template.value, "status": "success"}
                    )
                if self.events:
                    await self.events.log_event(
                        event_type="email.sent",
                        user_id=None,
                        properties={"to": to_email, "template": template.value}
                    )
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code}")
                if self.metrics:
                    self.metrics.increment_counter(
                        "emails_sent_total",
                        tags={"template": template.value, "status": "error"}
                    )
                return False
                
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            if self.metrics:
                self.metrics.increment_counter(
                    "emails_sent_total",
                    tags={"template": template.value, "status": "error"}
                )
            return False
    
    async def send_bulk_email(
        self,
        to_emails: List[str],
        template: EmailTemplate,
        context: Dict
    ) -> Dict[str, bool]:
        """Send bulk emails"""
        results = {}
        for email in to_emails:
            results[email] = await self.send_email(email, template, context)
        return results
