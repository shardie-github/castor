"""
User Metrics Aggregator

Aggregates user activity metrics (DAU/WAU/MAU, activation, retention) from events.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from src.database import PostgresConnection

logger = logging.getLogger(__name__)


@dataclass
class UserMetrics:
    """User metrics data structure"""
    dau: int
    wau: int
    mau: int
    activation_rate: float
    day_7_retention: float
    day_30_retention: float


class UserMetricsAggregator:
    """
    User Metrics Aggregator
    
    Aggregates user activity metrics from events table.
    """
    
    def __init__(self, postgres_conn: PostgresConnection):
        self.postgres_conn = postgres_conn
    
    async def get_dau(self, date: Optional[datetime] = None) -> int:
        """
        Get Daily Active Users
        
        Args:
            date: Date to calculate DAU for (defaults to today)
        
        Returns:
            Number of unique users active in last 24 hours
        """
        if date is None:
            date = datetime.now(timezone.utc)
        
        start_time = date - timedelta(days=1)
        
        query = """
            SELECT COUNT(DISTINCT user_id) as dau
            FROM events
            WHERE timestamp >= $1
              AND timestamp < $2
              AND user_id IS NOT NULL
        """
        
        row = await self.postgres_conn.fetch_one(query, start_time, date)
        return row["dau"] or 0 if row else 0
    
    async def get_wau(self, date: Optional[datetime] = None) -> int:
        """
        Get Weekly Active Users
        
        Args:
            date: Date to calculate WAU for (defaults to today)
        
        Returns:
            Number of unique users active in last 7 days
        """
        if date is None:
            date = datetime.now(timezone.utc)
        
        start_time = date - timedelta(days=7)
        
        query = """
            SELECT COUNT(DISTINCT user_id) as wau
            FROM events
            WHERE timestamp >= $1
              AND timestamp < $2
              AND user_id IS NOT NULL
        """
        
        row = await self.postgres_conn.fetch_one(query, start_time, date)
        return row["wau"] or 0 if row else 0
    
    async def get_mau(self, date: Optional[datetime] = None) -> int:
        """
        Get Monthly Active Users
        
        Args:
            date: Date to calculate MAU for (defaults to today)
        
        Returns:
            Number of unique users active in last 30 days
        """
        if date is None:
            date = datetime.now(timezone.utc)
        
        start_time = date - timedelta(days=30)
        
        query = """
            SELECT COUNT(DISTINCT user_id) as mau
            FROM events
            WHERE timestamp >= $1
              AND timestamp < $2
              AND user_id IS NOT NULL
        """
        
        row = await self.postgres_conn.fetch_one(query, start_time, date)
        return row["mau"] or 0 if row else 0
    
    async def get_activation_rate(
        self,
        days: int = 7,
        lookback_days: int = 30
    ) -> float:
        """
        Get activation rate (7-day by default)
        
        Activation = User completes onboarding AND generates first value
        (report, campaign, or attribution setup)
        
        Args:
            days: Days after signup to consider for activation (default: 7)
            lookback_days: How far back to look for signups (default: 30)
        
        Returns:
            Activation rate as percentage (0-100)
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=lookback_days)
        
        query = """
            WITH signups AS (
                SELECT user_id, MIN(timestamp) as signup_time
                FROM events
                WHERE event_type = 'onboarding_started'
                  AND timestamp >= $1
                  AND timestamp < $2
                GROUP BY user_id
            ),
            activations AS (
                SELECT DISTINCT user_id
                FROM events
                WHERE event_type IN (
                    'report_generated',
                    'campaign_launched',
                    'attribution_setup_completed',
                    'first_value_delivered'
                )
                AND timestamp >= $1
            )
            SELECT 
                COUNT(DISTINCT s.user_id) as total_signups,
                COUNT(DISTINCT a.user_id) as activated_users
            FROM signups s
            LEFT JOIN activations a ON s.user_id = a.user_id
                AND a.user_id IN (
                    SELECT user_id
                    FROM events
                    WHERE event_type IN (
                        'report_generated',
                        'campaign_launched',
                        'attribution_setup_completed',
                        'first_value_delivered'
                    )
                    AND timestamp <= s.signup_time + INTERVAL '%s days'
                )
        """ % days
        
        row = await self.postgres_conn.fetch_one(query, start_date, end_date)
        
        if not row or row["total_signups"] == 0:
            return 0.0
        
        activated = row["activated_users"] or 0
        total = row["total_signups"]
        
        return (activated / total * 100) if total > 0 else 0.0
    
    async def get_retention_rate(
        self,
        day: int = 7,
        lookback_days: int = 60
    ) -> float:
        """
        Get retention rate for specific day (Day 7 by default)
        
        Args:
            day: Day to calculate retention for (default: 7)
            lookback_days: How far back to look for activations (default: 60)
        
        Returns:
            Retention rate as percentage (0-100)
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=lookback_days)
        
        query = """
            WITH activations AS (
                SELECT user_id, MIN(timestamp) as activation_time
                FROM events
                WHERE event_type IN (
                    'report_generated',
                    'campaign_launched',
                    'attribution_setup_completed',
                    'first_value_delivered'
                )
                AND timestamp >= $1
                AND timestamp < $2
                GROUP BY user_id
            ),
            returns AS (
                SELECT DISTINCT a.user_id
                FROM activations a
                JOIN events e ON a.user_id = e.user_id
                WHERE e.timestamp >= a.activation_time + INTERVAL '%s days'
                  AND e.timestamp < a.activation_time + INTERVAL '%s days'
                  AND e.user_id IS NOT NULL
            )
            SELECT 
                COUNT(DISTINCT a.user_id) as total_activated,
                COUNT(DISTINCT r.user_id) as returned_users
            FROM activations a
            LEFT JOIN returns r ON a.user_id = r.user_id
        """ % (day, day + 1)
        
        row = await self.postgres_conn.fetch_one(query, start_date, end_date)
        
        if not row or row["total_activated"] == 0:
            return 0.0
        
        returned = row["returned_users"] or 0
        total = row["total_activated"]
        
        return (returned / total * 100) if total > 0 else 0.0
    
    async def get_all_metrics(self) -> UserMetrics:
        """Get all user metrics"""
        dau = await self.get_dau()
        wau = await self.get_wau()
        mau = await self.get_mau()
        activation_rate = await self.get_activation_rate()
        day_7_retention = await self.get_retention_rate(day=7)
        day_30_retention = await self.get_retention_rate(day=30)
        
        return UserMetrics(
            dau=dau,
            wau=wau,
            mau=mau,
            activation_rate=activation_rate,
            day_7_retention=day_7_retention,
            day_30_retention=day_30_retention
        )
