"""
Marketing Spend Tracker

Tracks marketing spend by channel for CAC calculation.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class MarketingChannel(str, Enum):
    """Marketing channels"""
    CONTENT_MARKETING = "content_marketing"
    PRODUCT_LED_GROWTH = "product_led_growth"
    COMMUNITY_MARKETING = "community_marketing"
    PAID_SOCIAL = "paid_social"
    PARTNERSHIPS = "partnerships"
    EMAIL_MARKETING = "email_marketing"
    EVENTS = "events"
    PR_MEDIA = "pr_media"
    SEO = "seo"
    REFERRAL = "referral"
    OTHER = "other"


@dataclass
class MarketingSpend:
    """Marketing spend data structure"""
    channel: str
    amount: float
    date: datetime
    description: Optional[str] = None


class MarketingSpendTracker:
    """
    Marketing Spend Tracker
    
    Tracks marketing spend by channel for CAC calculation.
    """
    
    def __init__(self, postgres_conn: PostgresConnection):
        self.postgres_conn = postgres_conn
    
    async def track_spend(
        self,
        channel: str,
        amount: float,
        date: Optional[datetime] = None,
        description: Optional[str] = None
    ):
        """
        Track marketing spend
        
        Args:
            channel: Marketing channel
            amount: Amount spent
            date: Date of spend (defaults to now)
            description: Optional description
        """
        if date is None:
            date = datetime.now(timezone.utc)
        
        query = """
            INSERT INTO marketing_spend (
                channel, amount, date, description, created_at
            )
            VALUES ($1, $2, $3, $4, NOW())
        """
        
        await self.postgres_conn.execute(
            query,
            channel,
            amount,
            date,
            description
        )
    
    async def get_total_spend(
        self,
        start_date: datetime,
        end_date: datetime,
        channel: Optional[str] = None
    ) -> float:
        """
        Get total marketing spend for a period
        
        Args:
            start_date: Start date
            end_date: End date
            channel: Optional channel filter
        
        Returns:
            Total spend
        """
        conditions = ["date >= $1", "date < $2"]
        params = [start_date, end_date]
        param_idx = 3
        
        if channel:
            conditions.append(f"channel = ${param_idx}")
            params.append(channel)
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT COALESCE(SUM(amount), 0) as total_spend
            FROM marketing_spend
            WHERE {where_clause}
        """
        
        row = await self.postgres_conn.fetch_one(query, *params)
        return float(row["total_spend"] or 0) if row else 0.0
    
    async def get_spend_by_channel(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """
        Get marketing spend by channel
        
        Args:
            start_date: Start date
            end_date: End date
        
        Returns:
            Dictionary mapping channel to spend
        """
        query = """
            SELECT channel, COALESCE(SUM(amount), 0) as total_spend
            FROM marketing_spend
            WHERE date >= $1 AND date < $2
            GROUP BY channel
        """
        
        rows = await self.postgres_conn.fetch_all(query, start_date, end_date)
        
        return {
            row["channel"]: float(row["total_spend"] or 0)
            for row in rows
        }
    
    async def calculate_cac(
        self,
        start_date: datetime,
        end_date: datetime,
        new_customers: int,
        channel: Optional[str] = None
    ) -> float:
        """
        Calculate Customer Acquisition Cost (CAC)
        
        Args:
            start_date: Start date
            end_date: End date
            new_customers: Number of new customers acquired
            channel: Optional channel filter
        
        Returns:
            CAC (spend / customers)
        """
        total_spend = await self.get_total_spend(start_date, end_date, channel)
        
        if new_customers == 0:
            return 0.0
        
        return total_spend / new_customers
