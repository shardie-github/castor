"""
Referral Program

Tracks referrals, calculates commissions, and manages payouts.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
import uuid

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class ReferralStatus(str, Enum):
    """Referral status"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CommissionStatus(str, Enum):
    """Commission payment status"""
    PENDING = "pending"
    CALCULATED = "calculated"
    PAID = "paid"
    CANCELLED = "cancelled"


@dataclass
class Referral:
    """Referral data model"""
    referral_id: str
    referrer_id: str  # Partner/user who made the referral
    referred_customer_id: Optional[str]  # Customer who was referred
    referral_code: str
    referral_link: str
    status: ReferralStatus
    first_year_commission_rate: float  # e.g., 0.20 for 20%
    recurring_commission_rate: float  # e.g., 0.10 for 10%
    total_commission_earned: float
    created_at: datetime
    converted_at: Optional[datetime]
    metadata: Dict


class ReferralProgram:
    """Manages referral tracking and commission calculation"""
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics_collector = metrics_collector
        self.event_logger = event_logger
    
    async def create_referral(
        self,
        referrer_id: str,
        referral_code: Optional[str] = None,
        first_year_rate: float = 0.20,
        recurring_rate: float = 0.10,
        metadata: Optional[Dict] = None
    ) -> Referral:
        """Create a new referral code/link"""
        referral_id = str(uuid.uuid4())
        
        if referral_code is None:
            referral_code = self._generate_referral_code(referrer_id)
        
        referral_link = f"https://app.example.com/signup?ref={referral_code}"
        
        referral = Referral(
            referral_id=referral_id,
            referrer_id=referrer_id,
            referred_customer_id=None,
            referral_code=referral_code,
            referral_link=referral_link,
            status=ReferralStatus.PENDING,
            first_year_commission_rate=first_year_rate,
            recurring_commission_rate=recurring_rate,
            total_commission_earned=0.0,
            created_at=datetime.utcnow(),
            converted_at=None,
            metadata=metadata or {}
        )
        
        await self._save_referral(referral)
        
        self.metrics_collector.increment_counter("referrals_created_total")
        self.event_logger.log_event("referral_created", {
            "referral_id": referral_id,
            "referrer_id": referrer_id,
            "referral_code": referral_code
        })
        
        logger.info(f"Created referral {referral_id} for referrer {referrer_id}")
        
        return referral
    
    async def track_referral_conversion(
        self,
        referral_code: str,
        customer_id: str,
        customer_revenue: float
    ) -> Optional[Referral]:
        """Track when a referral converts to a customer"""
        referral = await self.get_referral_by_code(referral_code)
        if not referral:
            logger.warning(f"Referral code not found: {referral_code}")
            return None
        
        if referral.status != ReferralStatus.PENDING:
            logger.warning(f"Referral {referral.referral_id} already converted")
            return referral
        
        referral.referred_customer_id = customer_id
        referral.status = ReferralStatus.ACTIVE
        referral.converted_at = datetime.utcnow()
        
        await self._save_referral(referral)
        
        # Calculate initial commission
        await self.calculate_commission(referral.referral_id, customer_revenue, is_first_year=True)
        
        self.metrics_collector.increment_counter("referrals_converted_total")
        self.event_logger.log_event("referral_converted", {
            "referral_id": referral.referral_id,
            "referrer_id": referral.referrer_id,
            "customer_id": customer_id,
            "revenue": customer_revenue
        })
        
        return referral
    
    async def calculate_commission(
        self,
        referral_id: str,
        revenue: float,
        is_first_year: bool = False
    ) -> float:
        """Calculate commission for a referral"""
        referral = await self.get_referral(referral_id)
        if not referral:
            return 0.0
        
        if is_first_year:
            commission_rate = referral.first_year_commission_rate
        else:
            commission_rate = referral.recurring_commission_rate
        
        commission = revenue * commission_rate
        
        # Update total commission
        referral.total_commission_earned += commission
        await self._save_referral(referral)
        
        # Record commission transaction
        commission_id = str(uuid.uuid4())
        query = """
            INSERT INTO referral_commissions (
                commission_id, referral_id, amount, revenue_amount,
                commission_rate, period_start, period_end, status, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        
        period_start = datetime.utcnow()
        period_end = period_start + timedelta(days=30)  # Monthly periods
        
        await self.postgres_conn.execute(
            query,
            commission_id,
            referral_id,
            commission,
            revenue,
            commission_rate,
            period_start,
            period_end,
            CommissionStatus.CALCULATED.value,
            datetime.utcnow()
        )
        
        self.metrics_collector.increment_counter("commissions_calculated_total", {
            "is_first_year": str(is_first_year)
        })
        
        return commission
    
    async def get_referral(self, referral_id: str) -> Optional[Referral]:
        """Get a referral by ID"""
        query = "SELECT * FROM referrals WHERE referral_id = $1"
        row = await self.postgres_conn.fetch_one(query, referral_id)
        if not row:
            return None
        return self._row_to_referral(row)
    
    async def get_referral_by_code(self, referral_code: str) -> Optional[Referral]:
        """Get a referral by code"""
        query = "SELECT * FROM referrals WHERE referral_code = $1"
        row = await self.postgres_conn.fetch_one(query, referral_code)
        if not row:
            return None
        return self._row_to_referral(row)
    
    async def list_referrals(
        self,
        referrer_id: Optional[str] = None,
        status: Optional[ReferralStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Referral]:
        """List referrals with filters"""
        conditions = []
        params = []
        param_idx = 1
        
        if referrer_id:
            conditions.append(f"referrer_id = ${param_idx}")
            params.append(referrer_id)
            param_idx += 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM referrals
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        
        params.extend([limit, offset])
        rows = await self.postgres_conn.fetch_all(query, *params)
        return [self._row_to_referral(row) for row in rows]
    
    async def get_referral_stats(self, referrer_id: str) -> Dict:
        """Get referral statistics for a referrer"""
        query = """
            SELECT 
                COUNT(*) as total_referrals,
                COUNT(*) FILTER (WHERE status = 'active') as active_referrals,
                COUNT(*) FILTER (WHERE status = 'completed') as completed_referrals,
                SUM(total_commission_earned) as total_commissions,
                COUNT(DISTINCT referred_customer_id) FILTER (WHERE referred_customer_id IS NOT NULL) as converted_count
            FROM referrals
            WHERE referrer_id = $1
        """
        
        row = await self.postgres_conn.fetch_one(query, referrer_id)
        
        return {
            "total_referrals": row["total_referrals"] or 0,
            "active_referrals": row["active_referrals"] or 0,
            "completed_referrals": row["completed_referrals"] or 0,
            "total_commissions": float(row["total_commissions"] or 0),
            "converted_count": row["converted_count"] or 0,
            "conversion_rate": (row["converted_count"] or 0) / max(row["total_referrals"] or 1, 1)
        }
    
    async def _save_referral(self, referral: Referral):
        """Save referral to database"""
        query = """
            INSERT INTO referrals (
                referral_id, referrer_id, referred_customer_id, referral_code,
                referral_link, status, first_year_commission_rate,
                recurring_commission_rate, total_commission_earned,
                created_at, converted_at, metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
            )
            ON CONFLICT (referral_id) DO UPDATE SET
                referred_customer_id = EXCLUDED.referred_customer_id,
                status = EXCLUDED.status,
                total_commission_earned = EXCLUDED.total_commission_earned,
                converted_at = EXCLUDED.converted_at,
                metadata = EXCLUDED.metadata
        """
        
        await self.postgres_conn.execute(
            query,
            referral.referral_id,
            referral.referrer_id,
            referral.referred_customer_id,
            referral.referral_code,
            referral.referral_link,
            referral.status.value,
            referral.first_year_commission_rate,
            referral.recurring_commission_rate,
            referral.total_commission_earned,
            referral.created_at,
            referral.converted_at,
            referral.metadata
        )
    
    def _generate_referral_code(self, referrer_id: str) -> str:
        """Generate a unique referral code"""
        # Simple implementation - in production, ensure uniqueness
        import hashlib
        hash_input = f"{referrer_id}{datetime.utcnow().isoformat()}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8].upper()
        return f"REF{hash_value}"
    
    def _row_to_referral(self, row: Dict) -> Referral:
        """Convert database row to Referral object"""
        return Referral(
            referral_id=row["referral_id"],
            referrer_id=row["referrer_id"],
            referred_customer_id=row.get("referred_customer_id"),
            referral_code=row["referral_code"],
            referral_link=row["referral_link"],
            status=ReferralStatus(row["status"]),
            first_year_commission_rate=float(row["first_year_commission_rate"]),
            recurring_commission_rate=float(row["recurring_commission_rate"]),
            total_commission_earned=float(row["total_commission_earned"] or 0),
            created_at=row["created_at"],
            converted_at=row.get("converted_at"),
            metadata=row.get("metadata", {})
        )
