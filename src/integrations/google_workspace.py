"""
Google Workspace Integration Module

Integrates with Google Workspace to:
- Send reports via Gmail
- Store reports in Google Drive
- Create calendar events for campaigns
- Share data via Google Sheets
"""

import logging
import aiohttp
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


@dataclass
class GoogleWorkspaceConfig:
    """Google Workspace API configuration"""
    client_id: str
    client_secret: str
    refresh_token: str
    access_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None


class GoogleWorkspaceIntegration:
    """
    Google Workspace Integration
    
    Handles:
    - Gmail integration
    - Google Drive storage
    - Google Calendar events
    - Google Sheets sharing
    """
    
    def __init__(
        self,
        config: GoogleWorkspaceConfig,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.config = config
        self.metrics = metrics_collector
        self.events = event_logger
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize HTTP session and refresh token if needed"""
        await self._ensure_valid_token()
        
        timeout = aiohttp.ClientTimeout(total=30)
        headers = {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/json"
        }
        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def _ensure_valid_token(self):
        """Ensure access token is valid, refresh if needed"""
        if (self.config.access_token and
            self.config.token_expires_at and
            self.config.token_expires_at > datetime.now(timezone.utc)):
            return
        
        # Refresh token
        await self._refresh_access_token()
    
    async def _refresh_access_token(self):
        """Refresh Google OAuth access token"""
        url = "https://oauth2.googleapis.com/token"
        
        payload = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": self.config.refresh_token,
            "grant_type": "refresh_token"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as response:
                response.raise_for_status()
                data = await response.json()
                
                self.config.access_token = data["access_token"]
                expires_in = data.get("expires_in", 3600)
                self.config.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send email via Gmail API"""
        await self._ensure_valid_token()
        
        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        
        # Create email message
        message = self._create_email_message(to, subject, body, attachments)
        
        payload = {
            "raw": message
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                response.raise_for_status()
                
                # Record telemetry
                self.metrics.increment_counter(
                    "google_workspace_email_sent",
                    tags={"to": to}
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Error sending Gmail: {e}")
            self.metrics.increment_counter(
                "google_workspace_api_errors",
                tags={"operation": "send_email", "error_type": type(e).__name__}
            )
            return False
    
    async def upload_to_drive(
        self,
        file_name: str,
        file_content: bytes,
        folder_id: Optional[str] = None
    ) -> Optional[str]:
        """Upload file to Google Drive"""
        await self._ensure_valid_token()
        
        url = "https://www.googleapis.com/upload/drive/v3/files"
        params = {"uploadType": "multipart"}
        
        # Create metadata
        metadata = {
            "name": file_name
        }
        if folder_id:
            metadata["parents"] = [folder_id]
        
        # Create multipart form data
        form_data = aiohttp.FormData()
        form_data.add_field(
            "metadata",
            aiohttp.JsonPayload(metadata),
            content_type="application/json"
        )
        form_data.add_field(
            "file",
            file_content,
            filename=file_name
        )
        
        try:
            async with self.session.post(url, params=params, data=form_data) as response:
                response.raise_for_status()
                data = await response.json()
                
                file_id = data.get("id")
                
                # Record telemetry
                self.metrics.increment_counter(
                    "google_workspace_file_uploaded",
                    tags={"file_name": file_name}
                )
                
                return file_id
                
        except Exception as e:
            logger.error(f"Error uploading to Google Drive: {e}")
            self.metrics.increment_counter(
                "google_workspace_api_errors",
                tags={"operation": "upload_to_drive", "error_type": type(e).__name__}
            )
            return None
    
    def _create_email_message(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Create email message in RFC 2822 format"""
        import base64
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        message = MIMEMultipart()
        message["To"] = to
        message["Subject"] = subject
        
        message.attach(MIMEText(body, "html"))
        
        # Add attachments if any
        if attachments:
            for attachment in attachments:
                # Handle attachments (simplified)
                pass
        
        # Encode message
        raw_message = message.as_string()
        return base64.urlsafe_b64encode(raw_message.encode("utf-8")).decode("utf-8")
