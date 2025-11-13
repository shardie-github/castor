"""
User-Driven Flows Module

Handles self-serve user flows including:
- Data export
- Billing management
- Account deletion
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.users.user_manager import UserManager, User
from src.campaigns.campaign_manager import CampaignManager
from src.analytics.analytics_store import AnalyticsStore
from src.reporting.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class FlowType(Enum):
    """User flow types"""
    EXPORT = "export"
    BILLING = "billing"
    DELETION = "deletion"
    SUBSCRIPTION_CHANGE = "subscription_change"
    DATA_DOWNLOAD = "data_download"


class ExportFormat(Enum):
    """Export formats"""
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    PDF = "pdf"
    SQL = "sql"


class DeletionStatus(Enum):
    """Account deletion status"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ExportRequest:
    """Data export request"""
    export_id: str
    user_id: str
    format: ExportFormat
    data_types: List[str]  # campaigns, analytics, reports, etc.
    status: str = "pending"  # pending, processing, completed, failed
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    file_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeletionRequest:
    """Account deletion request"""
    deletion_id: str
    user_id: str
    status: DeletionStatus
    scheduled_at: Optional[datetime] = None
    reason: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExportManager:
    """
    Export Manager
    
    Handles self-serve data export requests.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        user_manager: UserManager,
        campaign_manager: CampaignManager,
        analytics_store: AnalyticsStore,
        report_generator: ReportGenerator
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.users = user_manager
        self.campaigns = campaign_manager
        self.analytics = analytics_store
        self.reports = report_generator
        self._exports: Dict[str, ExportRequest] = {}
        
    async def create_export_request(
        self,
        user_id: str,
        format: ExportFormat,
        data_types: List[str],
        date_range: Optional[Dict[str, datetime]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExportRequest:
        """
        Create a data export request
        
        Args:
            user_id: User ID
            format: Export format
            data_types: Types of data to export (campaigns, analytics, reports, etc.)
            date_range: Optional date range filter
            metadata: Optional metadata
            
        Returns:
            ExportRequest
        """
        export_id = str(uuid4())
        
        export = ExportRequest(
            export_id=export_id,
            user_id=user_id,
            format=format,
            data_types=data_types,
            status="pending",
            metadata={
                **(metadata or {}),
                "date_range": date_range
            }
        )
        
        self._exports[export_id] = export
        
        # Process export asynchronously
        asyncio.create_task(self._process_export(export))
        
        # Record metrics
        self.metrics.increment_counter(
            "export_request_created",
            tags={"format": format.value, "user_id": user_id}
        )
        
        # Log event
        await self.events.log_event(
            event_type="export_requested",
            user_id=user_id,
            properties={
                "export_id": export_id,
                "format": format.value,
                "data_types": data_types
            }
        )
        
        return export
    
    async def _process_export(self, export: ExportRequest):
        """Process export request"""
        try:
            export.status = "processing"
            
            # Collect data based on data_types
            export_data = {}
            
            for data_type in export.data_types:
                if data_type == "campaigns":
                    campaigns = await self.campaigns.list_campaigns()
                    export_data["campaigns"] = [
                        {
                            "campaign_id": c.campaign_id,
                            "name": c.name,
                            "status": c.status.value,
                            "start_date": c.start_date.isoformat(),
                            "end_date": c.end_date.isoformat(),
                            "campaign_value": c.campaign_value
                        }
                        for c in campaigns
                    ]
                
                elif data_type == "analytics":
                    # Export analytics data
                    export_data["analytics"] = {
                        "note": "Analytics data export (simplified)"
                    }
                
                elif data_type == "reports":
                    # Export reports
                    reports = await self.reports.list_reports(user_id=export.user_id)
                    export_data["reports"] = [
                        {
                            "report_id": r.report_id,
                            "campaign_id": r.campaign_id,
                            "format": r.format.value,
                            "generated_at": r.generated_at.isoformat()
                        }
                        for r in reports
                    ]
            
            # Generate file based on format
            file_url, file_size = await self._generate_export_file(export, export_data)
            
            export.status = "completed"
            export.completed_at = datetime.now(timezone.utc)
            export.file_url = file_url
            export.file_size_bytes = file_size
            
            # Record metrics
            self.metrics.record_histogram(
                "export_file_size_bytes",
                file_size,
                tags={"format": export.format.value}
            )
            
            self.metrics.increment_counter(
                "export_completed",
                tags={"format": export.format.value}
            )
            
        except Exception as e:
            export.status = "failed"
            export.error_message = str(e)
            
            logger.error(f"Export {export.export_id} failed: {e}")
            
            self.metrics.increment_counter(
                "export_failed",
                tags={"format": export.format.value, "error": type(e).__name__}
            )
    
    async def _generate_export_file(
        self,
        export: ExportRequest,
        data: Dict[str, Any]
    ) -> tuple[str, int]:
        """Generate export file"""
        # In production, would generate actual files:
        # - CSV: Use csv module
        # - JSON: Use json module
        # - Excel: Use openpyxl or xlsxwriter
        # - PDF: Use report generator
        # - SQL: Generate SQL dump
        
        file_url = f"/exports/{export.export_id}.{export.format.value}"
        file_size = 1024 * 50  # Placeholder
        
        return file_url, file_size
    
    async def get_export(self, export_id: str) -> Optional[ExportRequest]:
        """Get export request by ID"""
        return self._exports.get(export_id)
    
    async def list_exports(self, user_id: str) -> List[ExportRequest]:
        """List exports for a user"""
        return [e for e in self._exports.values() if e.user_id == user_id]


class BillingManager:
    """
    Billing Manager
    
    Handles self-serve billing operations.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        user_manager: UserManager
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.users = user_manager
        
    async def get_billing_info(self, user_id: str) -> Dict[str, Any]:
        """Get billing information for user"""
        user = await self.users.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # In production, would fetch from billing system
        return {
            "user_id": user_id,
            "subscription_tier": user.subscription_tier.value,
            "billing_email": user.email,
            "current_period_start": datetime.now(timezone.utc).isoformat(),
            "current_period_end": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "amount": self._get_tier_price(user.subscription_tier),
            "currency": "USD",
            "payment_method": "card_ending_1234",  # Placeholder
            "invoices": []
        }
    
    def _get_tier_price(self, tier) -> float:
        """Get price for subscription tier"""
        prices = {
            "free": 0.0,
            "starter": 29.0,
            "professional": 99.0,
            "enterprise": 0.0  # Custom pricing
        }
        return prices.get(tier.value, 0.0)
    
    async def update_payment_method(
        self,
        user_id: str,
        payment_method_id: str
    ) -> Dict[str, Any]:
        """Update payment method"""
        # In production, would integrate with payment processor
        
        await self.events.log_event(
            event_type="payment_method_updated",
            user_id=user_id,
            properties={"payment_method_id": payment_method_id}
        )
        
        self.metrics.increment_counter("payment_method_updated", tags={"user_id": user_id})
        
        return {"status": "success", "message": "Payment method updated"}
    
    async def cancel_subscription(
        self,
        user_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel subscription"""
        user = await self.users.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Update user to free tier
        await self.users.update_user(user_id, {"subscription_tier": "free"})
        
        await self.events.log_event(
            event_type="subscription_cancelled",
            user_id=user_id,
            properties={"reason": reason, "previous_tier": user.subscription_tier.value}
        )
        
        self.metrics.increment_counter("subscription_cancelled", tags={"user_id": user_id})
        
        return {"status": "success", "message": "Subscription cancelled"}
    
    async def upgrade_subscription(
        self,
        user_id: str,
        new_tier: str
    ) -> Dict[str, Any]:
        """Upgrade subscription"""
        user = await self.users.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        old_tier = user.subscription_tier.value
        
        await self.users.update_user(user_id, {"subscription_tier": new_tier})
        
        await self.events.log_event(
            event_type="subscription_upgraded",
            user_id=user_id,
            properties={"old_tier": old_tier, "new_tier": new_tier}
        )
        
        self.metrics.increment_counter(
            "subscription_upgraded",
            tags={"from": old_tier, "to": new_tier}
        )
        
        return {"status": "success", "message": f"Upgraded to {new_tier}"}


class AccountDeletionManager:
    """
    Account Deletion Manager
    
    Handles account deletion requests with proper data retention and compliance.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        user_manager: UserManager,
        campaign_manager: CampaignManager
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.users = user_manager
        self.campaigns = campaign_manager
        self._deletion_requests: Dict[str, DeletionRequest] = {}
        
    async def request_deletion(
        self,
        user_id: str,
        reason: Optional[str] = None,
        immediate: bool = False
    ) -> DeletionRequest:
        """
        Request account deletion
        
        Args:
            user_id: User ID
            reason: Optional reason for deletion
            immediate: If True, delete immediately; otherwise schedule for 30 days
            
        Returns:
            DeletionRequest
        """
        deletion_id = str(uuid4())
        
        if immediate:
            status = DeletionStatus.IN_PROGRESS
            scheduled_at = None
        else:
            status = DeletionStatus.SCHEDULED
            scheduled_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        deletion = DeletionRequest(
            deletion_id=deletion_id,
            user_id=user_id,
            status=status,
            scheduled_at=scheduled_at,
            reason=reason
        )
        
        self._deletion_requests[deletion_id] = deletion
        
        if immediate:
            asyncio.create_task(self._execute_deletion(deletion))
        else:
            # Schedule deletion
            asyncio.create_task(self._schedule_deletion(deletion))
        
        await self.events.log_event(
            event_type="account_deletion_requested",
            user_id=user_id,
            properties={
                "deletion_id": deletion_id,
                "immediate": immediate,
                "scheduled_at": scheduled_at.isoformat() if scheduled_at else None
            }
        )
        
        self.metrics.increment_counter(
            "account_deletion_requested",
            tags={"immediate": str(immediate)}
        )
        
        return deletion
    
    async def _schedule_deletion(self, deletion: DeletionRequest):
        """Schedule deletion for later"""
        if not deletion.scheduled_at:
            return
        
        wait_time = (deletion.scheduled_at - datetime.now(timezone.utc)).total_seconds()
        
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        
        await self._execute_deletion(deletion)
    
    async def _execute_deletion(self, deletion: DeletionRequest):
        """Execute account deletion"""
        try:
            deletion.status = DeletionStatus.IN_PROGRESS
            
            user = await self.users.get_user(deletion.user_id)
            if not user:
                deletion.status = DeletionStatus.COMPLETED
                return
            
            # In production, would:
            # 1. Export user data (for compliance)
            # 2. Anonymize or delete personal data
            # 3. Retain aggregated/anonymized analytics (if allowed)
            # 4. Delete user account
            # 5. Delete associated campaigns (or transfer ownership)
            # 6. Delete reports
            # 7. Log deletion for audit
            
            # Mark user as deleted
            await self.users.update_user(deletion.user_id, {"is_active": False})
            
            deletion.status = DeletionStatus.COMPLETED
            deletion.completed_at = datetime.now(timezone.utc)
            
            await self.events.log_event(
                event_type="account_deleted",
                user_id=deletion.user_id,
                properties={"deletion_id": deletion.deletion_id}
            )
            
            self.metrics.increment_counter("account_deleted", tags={"user_id": deletion.user_id})
            
        except Exception as e:
            logger.error(f"Account deletion {deletion.deletion_id} failed: {e}")
            deletion.metadata["error"] = str(e)
    
    async def cancel_deletion(self, deletion_id: str) -> DeletionRequest:
        """Cancel scheduled deletion"""
        deletion = self._deletion_requests.get(deletion_id)
        if not deletion:
            raise ValueError(f"Deletion request {deletion_id} not found")
        
        if deletion.status == DeletionStatus.COMPLETED:
            raise ValueError("Cannot cancel completed deletion")
        
        deletion.status = DeletionStatus.CANCELLED
        
        await self.events.log_event(
            event_type="account_deletion_cancelled",
            user_id=deletion.user_id,
            properties={"deletion_id": deletion_id}
        )
        
        return deletion
    
    async def get_deletion_request(self, deletion_id: str) -> Optional[DeletionRequest]:
        """Get deletion request by ID"""
        return self._deletion_requests.get(deletion_id)


class UserFlowManager:
    """
    User Flow Manager
    
    Coordinates all user-driven flows.
    """
    
    def __init__(
        self,
        export_manager: ExportManager,
        billing_manager: BillingManager,
        deletion_manager: AccountDeletionManager
    ):
        self.exports = export_manager
        self.billing = billing_manager
        self.deletion = deletion_manager
