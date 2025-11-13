"""
DELTA:20251113_064143 Affiliate Manager

Manages affiliate marketing program, referrals, and commissions.
"""

import logging
import secrets
import string
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class AffiliateManager:
    """DELTA:20251113_064143 Affiliate manager"""
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics = metrics_collector
        self.events = event_logger
    
    def _generate_referral_code(self) -> str:
        """DELTA:20251113_064143 Generate unique referral code"""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    
    async def create_affiliate(
        self,
        tenant_id: str,
        name: str,
        email: Optional[str] = None,
        agency_id: Optional[str] = None,
        commission_rate_percent: float = 10.0
    ) -> Dict[str, Any]:
        """DELTA:20251113_064143 Create affiliate"""
        # Generate unique referral code
        referral_code = self._generate_referral_code()
        
        # Ensure uniqueness
        while await self._referral_code_exists(referral_code):
            referral_code = self._generate_referral_code()
        
        query = """
            INSERT INTO affiliates (
                tenant_id, agency_id, name, email, referral_code, commission_rate_percent
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6)
            RETURNING affiliate_id, referral_code;
        """
        
        row = await self.postgres_conn.fetchrow(
            query,
            tenant_id, agency_id, name, email, referral_code, commission_rate_percent
        )
        
        affiliate_id = str(row['affiliate_id'])
        
        await self.events.log_event(
            event_type='affiliate.created',
            user_id=None,
            properties={
                'affiliate_id': affiliate_id,
                'referral_code': referral_code
            }
        )
        
        return {
            'affiliate_id': affiliate_id,
            'referral_code': referral_code
        }
    
    async def _referral_code_exists(self, referral_code: str) -> bool:
        """DELTA:20251113_064143 Check if referral code exists"""
        query = "SELECT 1 FROM affiliates WHERE referral_code = $1 LIMIT 1;"
        row = await self.postgres_conn.fetchrow(query, referral_code)
        return row is not None
    
    async def track_referral(
        self,
        tenant_id: str,
        referral_code: str,
        referred_tenant_id: Optional[str] = None
    ) -> str:
        """DELTA:20251113_064143 Track referral"""
        # Find affiliate by referral code
        query = """
            SELECT affiliate_id FROM affiliates
            WHERE referral_code = $1 AND status = 'active';
        """
        affiliate_row = await self.postgres_conn.fetchrow(query, referral_code)
        
        if not affiliate_row:
            raise ValueError(f"Invalid referral code: {referral_code}")
        
        affiliate_id = str(affiliate_row['affiliate_id'])
        
        # Create referral record
        insert_query = """
            INSERT INTO referrals (
                tenant_id, affiliate_id, referral_code, referred_tenant_id
            )
            VALUES ($1::uuid, $2::uuid, $3, $4::uuid)
            RETURNING referral_id;
        """
        
        row = await self.postgres_conn.fetchrow(
            insert_query,
            tenant_id, affiliate_id, referral_code, referred_tenant_id
        )
        
        referral_id = str(row['referral_id'])
        
        await self.events.log_event(
            event_type='referral.tracked',
            user_id=None,
            properties={
                'referral_id': referral_id,
                'affiliate_id': affiliate_id,
                'referral_code': referral_code
            }
        )
        
        return referral_id
    
    async def convert_referral(
        self,
        referral_id: str,
        tenant_id: str,
        conversion_value_cents: int
    ) -> Dict[str, Any]:
        """DELTA:20251113_064143 Convert referral (when referred tenant subscribes)"""
        # Get referral and affiliate info
        query = """
            SELECT r.affiliate_id, r.referral_code, a.commission_rate_percent
            FROM referrals r
            JOIN affiliates a ON a.affiliate_id = r.affiliate_id
            WHERE r.referral_id = $1::uuid AND r.tenant_id = $2::uuid;
        """
        
        row = await self.postgres_conn.fetchrow(query, referral_id, tenant_id)
        
        if not row:
            raise ValueError("Referral not found")
        
        commission_rate = float(row['commission_rate_percent'])
        commission_cents = int(conversion_value_cents * (commission_rate / 100))
        
        # Update referral
        update_query = """
            UPDATE referrals
            SET conversion_status = 'converted',
                conversion_value_cents = $1,
                commission_cents = $2,
                converted_at = NOW()
            WHERE referral_id = $3::uuid;
        """
        
        await self.postgres_conn.execute(
            update_query,
            conversion_value_cents, commission_cents, referral_id
        )
        
        # Update affiliate stats
        update_affiliate_query = """
            UPDATE affiliates
            SET total_referrals = total_referrals + 1,
                total_commission_cents = total_commission_cents + $1,
                updated_at = NOW()
            WHERE affiliate_id = $2::uuid;
        """
        
        await self.postgres_conn.execute(
            update_affiliate_query,
            commission_cents, row['affiliate_id']
        )
        
        await self.events.log_event(
            event_type='referral.converted',
            user_id=None,
            properties={
                'referral_id': referral_id,
                'affiliate_id': str(row['affiliate_id']),
                'conversion_value_cents': conversion_value_cents,
                'commission_cents': commission_cents
            }
        )
        
        return {
            'referral_id': referral_id,
            'commission_cents': commission_cents,
            'conversion_value_cents': conversion_value_cents
        }
    
    async def get_affiliate_stats(self, affiliate_id: str, tenant_id: str) -> Dict[str, Any]:
        """DELTA:20251113_064143 Get affiliate statistics"""
        query = """
            SELECT 
                a.affiliate_id, a.name, a.referral_code, a.commission_rate_percent,
                a.total_referrals, a.total_commission_cents,
                COUNT(r.referral_id) FILTER (WHERE r.conversion_status = 'converted') as converted_count,
                COUNT(r.referral_id) FILTER (WHERE r.conversion_status = 'pending') as pending_count,
                SUM(r.conversion_value_cents) FILTER (WHERE r.conversion_status = 'converted') as total_conversion_value
            FROM affiliates a
            LEFT JOIN referrals r ON r.affiliate_id = a.affiliate_id
            WHERE a.affiliate_id = $1::uuid AND a.tenant_id = $2::uuid
            GROUP BY a.affiliate_id;
        """
        
        row = await self.postgres_conn.fetchrow(query, affiliate_id, tenant_id)
        
        if not row:
            return {}
        
        return {
            'affiliate_id': str(row['affiliate_id']),
            'name': row['name'],
            'referral_code': row['referral_code'],
            'commission_rate_percent': float(row['commission_rate_percent']),
            'total_referrals': row['total_referrals'],
            'total_commission_cents': row['total_commission_cents'] or 0,
            'converted_count': row['converted_count'] or 0,
            'pending_count': row['pending_count'] or 0,
            'total_conversion_value': row['total_conversion_value'] or 0
        }
