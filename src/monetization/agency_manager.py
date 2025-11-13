"""
DELTA:20251113_064143 Agency Manager

Manages agency/consultancy relationships and commissions.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class AgencyManager:
    """DELTA:20251113_064143 Agency manager"""
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics = metrics_collector
        self.events = event_logger
    
    async def create_agency(
        self,
        tenant_id: str,
        name: str,
        slug: str,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        commission_rate_percent: float = 0.0
    ) -> str:
        """DELTA:20251113_064143 Create agency"""
        query = """
            INSERT INTO agencies (
                tenant_id, name, slug, contact_email, contact_phone, commission_rate_percent
            )
            VALUES ($1::uuid, $2, $3, $4, $5, $6)
            RETURNING agency_id;
        """
        
        row = await self.postgres_conn.fetchrow(
            query,
            tenant_id, name, slug, contact_email, contact_phone, commission_rate_percent
        )
        
        agency_id = str(row['agency_id'])
        
        await self.events.log_event(
            event_type='agency.created',
            user_id=None,
            properties={
                'agency_id': agency_id,
                'name': name,
                'slug': slug
            }
        )
        
        return agency_id
    
    async def get_agency(self, agency_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """DELTA:20251113_064143 Get agency"""
        query = """
            SELECT agency_id, tenant_id, name, slug, contact_email, contact_phone,
                   commission_rate_percent, status, created_at, updated_at, metadata
            FROM agencies
            WHERE agency_id = $1::uuid AND tenant_id = $2::uuid;
        """
        
        row = await self.postgres_conn.fetchrow(query, agency_id, tenant_id)
        
        if not row:
            return None
        
        return {
            'agency_id': str(row['agency_id']),
            'tenant_id': str(row['tenant_id']),
            'name': row['name'],
            'slug': row['slug'],
            'contact_email': row['contact_email'],
            'contact_phone': row['contact_phone'],
            'commission_rate_percent': float(row['commission_rate_percent']),
            'status': row['status'],
            'created_at': row['created_at'].isoformat(),
            'updated_at': row['updated_at'].isoformat(),
            'metadata': row['metadata']
        }
    
    async def list_agencies(self, tenant_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """DELTA:20251113_064143 List agencies"""
        if status:
            query = """
                SELECT agency_id, name, slug, contact_email, commission_rate_percent, status
                FROM agencies
                WHERE tenant_id = $1::uuid AND status = $2
                ORDER BY created_at DESC;
            """
            rows = await self.postgres_conn.fetch(query, tenant_id, status)
        else:
            query = """
                SELECT agency_id, name, slug, contact_email, commission_rate_percent, status
                FROM agencies
                WHERE tenant_id = $1::uuid
                ORDER BY created_at DESC;
            """
            rows = await self.postgres_conn.fetch(query, tenant_id)
        
        return [
            {
                'agency_id': str(row['agency_id']),
                'name': row['name'],
                'slug': row['slug'],
                'contact_email': row['contact_email'],
                'commission_rate_percent': float(row['commission_rate_percent']),
                'status': row['status']
            }
            for row in rows
        ]
    
    async def calculate_commission(
        self,
        agency_id: str,
        tenant_id: str,
        transaction_amount_cents: int
    ) -> Dict[str, Any]:
        """DELTA:20251113_064143 Calculate commission for agency"""
        agency = await self.get_agency(agency_id, tenant_id)
        
        if not agency or agency['status'] != 'active':
            return {'commission_cents': 0, 'rate': 0.0}
        
        commission_rate = agency['commission_rate_percent']
        commission_cents = int(transaction_amount_cents * (commission_rate / 100))
        
        return {
            'commission_cents': commission_cents,
            'rate': commission_rate,
            'agency_id': agency_id
        }
