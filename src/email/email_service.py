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
try:
    import boto3
    from botocore.exceptions import ClientError
    SES_AVAILABLE = True
except ImportError:
    SES_AVAILABLE = False

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpen,
    get_circuit_breaker
)
from src.utils.retry import retry_with_backoff, RETRY_CONFIGS

logger = logging.getLogger(__name__)

# Circuit breaker for SendGrid API
_sendgrid_circuit_breaker = get_circuit_breaker(
    "sendgrid",
    CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout_seconds=60.0,
        expected_exception=Exception
    )
)


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
        event_logger: Optional[EventLogger] = None,
        aws_region: Optional[str] = None
    ):
        self.provider = provider
        self.from_email = from_email or os.getenv("FROM_EMAIL", "noreply@podcastanalytics.com")
        self.metrics = metrics_collector
        self.events = event_logger
        self.client = None
        
        if provider == EmailProvider.SENDGRID:
            self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
            if self.api_key:
                self.client = SendGridAPIClient(self.api_key)
            else:
                logger.warning("SendGrid API key not found")
        elif provider == EmailProvider.SES:
            if not SES_AVAILABLE:
                logger.error("boto3 not installed. Install with: pip install boto3")
                return
            
            aws_access_key = api_key or os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            aws_region = aws_region or os.getenv("AWS_REGION", "us-east-1")
            
            if aws_access_key and aws_secret_key:
                self.client = boto3.client(
                    'ses',
                    region_name=aws_region,
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key
                )
            else:
                logger.warning("AWS credentials not found for SES")
    
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
        """Send an email with circuit breaker and retry logic"""
        try:
            if not self.client:
                logger.error("Email client not initialized")
                return False
            
            email_subject, email_body = self._get_template_content(template, context)
            
            if subject:
                email_subject = subject
            if body:
                email_body = body
            
            if self.provider == EmailProvider.SENDGRID:
                return await self._send_sendgrid(to_email, email_subject, email_body, template)
            elif self.provider == EmailProvider.SES:
                return await self._send_ses(to_email, email_subject, email_body, template)
            else:
                logger.error(f"Unknown email provider: {self.provider}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            if self.metrics:
                self.metrics.increment_counter(
                    "emails_sent_total",
                    tags={"template": template.value, "status": "error"}
                )
            return False
    
    async def _send_sendgrid(
        self,
        to_email: str,
        subject: str,
        body: str,
        template: EmailTemplate
    ) -> bool:
        """Send email via SendGrid"""
        async def _send():
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", body)
            )
            
            response = self.client.send(message)
            
            if response.status_code not in [200, 202]:
                raise Exception(f"SendGrid API returned status {response.status_code}")
            
            return True
        
        try:
            result = await _sendgrid_circuit_breaker.call(_send)
            
            if self.metrics:
                self.metrics.increment_counter(
                    "emails_sent_total",
                    tags={"template": template.value, "status": "success", "provider": "sendgrid"}
                )
            if self.events:
                await self.events.log_event(
                    event_type="email.sent",
                    user_id=None,
                    properties={"to": to_email, "template": template.value, "provider": "sendgrid"}
                )
            return result
            
        except CircuitBreakerOpen as e:
            logger.error(f"Circuit breaker open for SendGrid: {e}")
            if self.metrics:
                self.metrics.increment_counter(
                    "emails_sent_total",
                    tags={"template": template.value, "status": "circuit_open", "provider": "sendgrid"}
                )
            return False
    
    async def _send_ses(
        self,
        to_email: str,
        subject: str,
        body: str,
        template: EmailTemplate
    ) -> bool:
        """Send email via AWS SES"""
        try:
            response = self.client.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [to_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {'Html': {'Data': body, 'Charset': 'UTF-8'}}
                }
            )
            
            if self.metrics:
                self.metrics.increment_counter(
                    "emails_sent_total",
                    tags={"template": template.value, "status": "success", "provider": "ses"}
                )
            if self.events:
                await self.events.log_event(
                    event_type="email.sent",
                    user_id=None,
                    properties={"to": to_email, "template": template.value, "provider": "ses"}
                )
            
            logger.info(f"Email sent via SES: {response['MessageId']}")
            return True
            
        except ClientError as e:
            logger.error(f"AWS SES error: {str(e)}")
            if self.metrics:
                self.metrics.increment_counter(
                    "emails_sent_total",
                    tags={"template": template.value, "status": "error", "provider": "ses"}
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
