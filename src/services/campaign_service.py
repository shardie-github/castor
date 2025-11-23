"""
Campaign Service

Business logic for campaign management, separated from API routes.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.utils.error_responses import NotFoundError, ValidationError, ConflictError

logger = logging.getLogger(__name__)


class CampaignService:
    """Service for campaign business logic"""
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics = metrics_collector
        self.events = event_logger
    
    async def create_campaign(
        self,
        tenant_id: str,
        user_id: str,
        campaign_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new campaign"""
        # Validate podcast belongs to tenant
        podcast = await self.postgres_conn.fetchrow(
            """
            SELECT podcast_id, tenant_id
            FROM podcasts
            WHERE podcast_id = $1 AND tenant_id = $2
            """,
            campaign_data['podcast_id'],
            tenant_id
        )
        
        if not podcast:
            raise NotFoundError("podcast", campaign_data['podcast_id'])
        
        # Validate dates
        start_date = campaign_data.get('start_date')
        end_date = campaign_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError("End date must be after start date")
        
        # Create campaign
        query = """
            INSERT INTO campaigns (
                tenant_id, podcast_id, sponsor_id, name,
                start_date, end_date, campaign_value, status,
                attribution_method, promo_code, created_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING campaign_id, tenant_id, podcast_id, sponsor_id, name,
                      status, start_date, end_date, campaign_value,
                      created_at, updated_at
        """
        
        campaign = await self.postgres_conn.fetchrow(
            query,
            tenant_id,
            campaign_data['podcast_id'],
            campaign_data.get('sponsor_id'),
            campaign_data['name'],
            start_date,
            end_date,
            campaign_data.get('campaign_value', 0),
            'draft',
            campaign_data.get('attribution_method', 'promo_code'),
            campaign_data.get('promo_code'),
            user_id
        )
        
        # Log event
        await self.events.log_event(
            event_type='campaign.created',
            user_id=user_id,
            properties={
                'campaign_id': str(campaign['campaign_id']),
                'tenant_id': tenant_id
            }
        )
        
        # Record metric
        self.metrics.increment_counter('campaigns_created_total', {
            'tenant_id': tenant_id
        })
        
        return dict(campaign)
    
    async def get_campaign(
        self,
        campaign_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """Get a campaign by ID"""
        campaign = await self.postgres_conn.fetchrow(
            """
            SELECT campaign_id, tenant_id, podcast_id, sponsor_id, name,
                   status, start_date, end_date, campaign_value,
                   created_at, updated_at
            FROM campaigns
            WHERE campaign_id = $1 AND tenant_id = $2
            """,
            campaign_id,
            tenant_id
        )
        
        if not campaign:
            raise NotFoundError("campaign", campaign_id)
        
        return dict(campaign)
    
    async def list_campaigns(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List campaigns for a tenant"""
        query = """
            SELECT campaign_id, tenant_id, podcast_id, sponsor_id, name,
                   status, start_date, end_date, campaign_value,
                   created_at, updated_at
            FROM campaigns
            WHERE tenant_id = $1
        """
        params = [tenant_id]
        
        if status:
            query += " AND status = $2"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT $2 OFFSET $3"
        params.extend([limit, offset])
        
        campaigns = await self.postgres_conn.fetch(query, *params)
        return [dict(campaign) for campaign in campaigns]
    
    async def update_campaign(
        self,
        campaign_id: str,
        tenant_id: str,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a campaign"""
        # Verify campaign exists and belongs to tenant
        campaign = await self.get_campaign(campaign_id, tenant_id)
        
        # Build update query
        updates = []
        params = []
        param_index = 1
        
        if 'name' in update_data:
            updates.append(f"name = ${param_index}")
            params.append(update_data['name'])
            param_index += 1
        
        if 'status' in update_data:
            updates.append(f"status = ${param_index}")
            params.append(update_data['status'])
            param_index += 1
        
        if 'start_date' in update_data:
            updates.append(f"start_date = ${param_index}")
            params.append(update_data['start_date'])
            param_index += 1
        
        if 'end_date' in update_data:
            updates.append(f"end_date = ${param_index}")
            params.append(update_data['end_date'])
            param_index += 1
        
        if 'campaign_value' in update_data:
            updates.append(f"campaign_value = ${param_index}")
            params.append(update_data['campaign_value'])
            param_index += 1
        
        if not updates:
            return campaign
        
        updates.append(f"updated_at = NOW()")
        params.extend([campaign_id, tenant_id])
        
        query = f"""
            UPDATE campaigns
            SET {', '.join(updates)}
            WHERE campaign_id = ${param_index} AND tenant_id = ${param_index + 1}
            RETURNING campaign_id, tenant_id, podcast_id, sponsor_id, name,
                      status, start_date, end_date, campaign_value,
                      created_at, updated_at
        """
        
        updated = await self.postgres_conn.fetchrow(query, *params)
        
        # Log event
        await self.events.log_event(
            event_type='campaign.updated',
            user_id=user_id,
            properties={
                'campaign_id': campaign_id,
                'tenant_id': tenant_id,
                'changes': list(update_data.keys())
            }
        )
        
        return dict(updated)
    
    async def delete_campaign(
        self,
        campaign_id: str,
        tenant_id: str,
        user_id: str
    ) -> None:
        """Delete a campaign"""
        # Verify campaign exists
        campaign = await self.get_campaign(campaign_id, tenant_id)
        
        # Delete campaign
        await self.postgres_conn.execute(
            """
            DELETE FROM campaigns
            WHERE campaign_id = $1 AND tenant_id = $2
            """,
            campaign_id,
            tenant_id
        )
        
        # Log event
        await self.events.log_event(
            event_type='campaign.deleted',
            user_id=user_id,
            properties={
                'campaign_id': campaign_id,
                'tenant_id': tenant_id
            }
        )
    
    async def get_campaign_analytics(
        self,
        campaign_id: str,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get analytics for a campaign"""
        # Verify campaign exists
        campaign = await self.get_campaign(campaign_id, tenant_id)
        
        # Get attribution events
        query = """
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT user_id) as unique_users,
                SUM(CASE WHEN event_type = 'conversion' THEN 1 ELSE 0 END) as conversions,
                SUM(CASE WHEN event_type = 'conversion' THEN revenue ELSE 0 END) as revenue
            FROM attribution_events
            WHERE campaign_id = $1 AND tenant_id = $2
        """
        params = [campaign_id, tenant_id]
        
        if start_date:
            query += " AND event_time >= $" + str(len(params) + 1)
            params.append(start_date)
        
        if end_date:
            query += " AND event_time <= $" + str(len(params) + 1)
            params.append(end_date)
        
        analytics = await self.postgres_conn.fetchrow(query, *params)
        
        # Calculate ROI
        revenue = analytics['revenue'] or 0
        campaign_value = campaign.get('campaign_value', 0)
        roi = ((revenue - campaign_value) / campaign_value * 100) if campaign_value > 0 else 0
        
        return {
            'campaign_id': campaign_id,
            'total_events': analytics['total_events'] or 0,
            'unique_users': analytics['unique_users'] or 0,
            'conversions': analytics['conversions'] or 0,
            'revenue': float(revenue),
            'roi': float(roi),
            'campaign_value': float(campaign_value)
        }
