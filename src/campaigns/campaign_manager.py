"""
Campaign Management Module

Handles sponsor/campaign management including:
- Campaign CRUD operations
- Sponsor relationship management
- Campaign lifecycle management
- Attribution setup
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector, LatencyTracker
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class CampaignStatus(Enum):
    """Campaign status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AttributionMethod(Enum):
    """Attribution methods"""
    PROMO_CODE = "promo_code"
    PIXEL = "pixel"
    UTM = "utm"
    CUSTOM = "custom"


@dataclass
class Sponsor:
    """Sponsor information"""
    sponsor_id: str
    name: str
    email: Optional[str] = None
    company: Optional[str] = None
    contact_name: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AttributionConfig:
    """Attribution configuration"""
    method: AttributionMethod
    promo_code: Optional[str] = None
    pixel_url: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    custom_tracking_id: Optional[str] = None
    conversion_endpoint: Optional[str] = None


@dataclass
class Campaign:
    """Campaign data structure"""
    campaign_id: str
    podcast_id: str
    sponsor_id: str
    name: str
    status: CampaignStatus
    start_date: datetime
    end_date: datetime
    attribution_config: AttributionConfig
    campaign_value: float  # Sponsorship fee
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    episode_ids: List[str] = field(default_factory=list)
    notes: Optional[str] = None


class CampaignManager:
    """
    Campaign Manager
    
    Manages sponsor campaigns with full lifecycle support.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        postgres_conn: Optional[PostgresConnection] = None
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.postgres = postgres_conn
        # Fallback to in-memory storage if no database connection
        self._use_db = postgres_conn is not None
        if not self._use_db:
            self._campaigns: Dict[str, Campaign] = {}
            self._sponsors: Dict[str, Sponsor] = {}
        
    async def create_campaign(
        self,
        user_id: str,
        podcast_id: str,
        sponsor_id: str,
        name: str,
        start_date: datetime,
        end_date: datetime,
        campaign_value: float,
        attribution_config: AttributionConfig,
        episode_ids: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> Campaign:
        """Create a new campaign"""
        with LatencyTracker(self.metrics, "campaign_creation_latency"):
            campaign_id = str(uuid4())
            
            campaign = Campaign(
                campaign_id=campaign_id,
                podcast_id=podcast_id,
                sponsor_id=sponsor_id,
                name=name,
                status=CampaignStatus.DRAFT,
                start_date=start_date,
                end_date=end_date,
                attribution_config=attribution_config,
                campaign_value=campaign_value,
                episode_ids=episode_ids or [],
                notes=notes
            )
            
            self._campaigns[campaign_id] = campaign
            
            # Record telemetry
            self.metrics.increment_counter(
                "campaign_created",
                tags={"podcast_id": podcast_id, "user_id": user_id}
            )
            
            # Log event
            await self.events.log_event(
                event_type="campaign_created",
                user_id=user_id,
                properties={
                    "campaign_id": campaign_id,
                    "podcast_id": podcast_id,
                    "sponsor_id": sponsor_id,
                    "campaign_value": campaign_value,
                    "attribution_method": attribution_config.method.value
                }
            )
            
            return campaign
    
    async def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get campaign by ID"""
        return self._campaigns.get(campaign_id)
    
    async def update_campaign(
        self,
        user_id: str,
        campaign_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Campaign]:
        """Update campaign"""
        campaign = self._campaigns.get(campaign_id)
        if not campaign:
            return None
        
        # Update fields
        if "name" in updates:
            campaign.name = updates["name"]
        if "start_date" in updates:
            campaign.start_date = updates["start_date"]
        if "end_date" in updates:
            campaign.end_date = updates["end_date"]
        if "status" in updates:
            campaign.status = CampaignStatus(updates["status"])
        if "attribution_config" in updates:
            campaign.attribution_config = updates["attribution_config"]
        if "episode_ids" in updates:
            campaign.episode_ids = updates["episode_ids"]
        if "notes" in updates:
            campaign.notes = updates["notes"]
        
        campaign.updated_at = datetime.now(timezone.utc)
        
        # Log event
        await self.events.log_event(
            event_type="campaign_updated",
            user_id=user_id,
            properties={
                "campaign_id": campaign_id,
                "updated_fields": list(updates.keys())
            }
        )
        
        return campaign
    
    async def delete_campaign(self, user_id: str, campaign_id: str) -> bool:
        """Delete campaign"""
        if campaign_id not in self._campaigns:
            return False
        
        del self._campaigns[campaign_id]
        
        # Log event
        await self.events.log_event(
            event_type="campaign_deleted",
            user_id=user_id,
            properties={"campaign_id": campaign_id}
        )
        
        return True
    
    async def list_campaigns(
        self,
        podcast_id: Optional[str] = None,
        sponsor_id: Optional[str] = None,
        status: Optional[CampaignStatus] = None
    ) -> List[Campaign]:
        """List campaigns with optional filters"""
        campaigns = list(self._campaigns.values())
        
        if podcast_id:
            campaigns = [c for c in campaigns if c.podcast_id == podcast_id]
        
        if sponsor_id:
            campaigns = [c for c in campaigns if c.sponsor_id == sponsor_id]
        
        if status:
            campaigns = [c for c in campaigns if c.status == status]
        
        return campaigns
    
    async def launch_campaign(self, user_id: str, campaign_id: str) -> Optional[Campaign]:
        """Launch a campaign (change status to active)"""
        campaign = self._campaigns.get(campaign_id)
        if not campaign:
            return None
        
        campaign.status = CampaignStatus.ACTIVE
        campaign.updated_at = datetime.now(timezone.utc)
        
        # Record telemetry
        self.metrics.increment_counter(
            "campaign_launched",
            tags={"campaign_id": campaign_id, "podcast_id": campaign.podcast_id}
        )
        
        # Log event
        await self.events.log_event(
            event_type="campaign_launched",
            user_id=user_id,
            properties={
                "campaign_id": campaign_id,
                "podcast_id": campaign.podcast_id,
                "on_time": datetime.now(timezone.utc) <= campaign.start_date
            }
        )
        
        return campaign
    
    async def complete_campaign(self, user_id: str, campaign_id: str) -> Optional[Campaign]:
        """Mark campaign as completed"""
        campaign = self._campaigns.get(campaign_id)
        if not campaign:
            return None
        
        campaign.status = CampaignStatus.COMPLETED
        campaign.updated_at = datetime.now(timezone.utc)
        
        # Log event
        await self.events.log_event(
            event_type="campaign_completed",
            user_id=user_id,
            properties={"campaign_id": campaign_id}
        )
        
        return campaign
    
    async def create_sponsor(
        self,
        user_id: str,
        name: str,
        email: Optional[str] = None,
        company: Optional[str] = None,
        contact_name: Optional[str] = None
    ) -> Sponsor:
        """Create a new sponsor"""
        sponsor_id = str(uuid4())
        
        sponsor = Sponsor(
            sponsor_id=sponsor_id,
            name=name,
            email=email,
            company=company,
            contact_name=contact_name
        )
        
        self._sponsors[sponsor_id] = sponsor
        
        # Log event
        await self.events.log_event(
            event_type="sponsor_created",
            user_id=user_id,
            properties={"sponsor_id": sponsor_id, "name": name}
        )
        
        return sponsor
    
    async def get_sponsor(self, sponsor_id: str) -> Optional[Sponsor]:
        """Get sponsor by ID"""
        return self._sponsors.get(sponsor_id)
    
    async def list_sponsors(self, user_id: Optional[str] = None) -> List[Sponsor]:
        """List all sponsors"""
        return list(self._sponsors.values())
