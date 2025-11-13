"""
DELTA:20251113_064143 API Usage Tracker

Tracks API calls for billing and rate limiting.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class APIUsageTracker:
    """DELTA:20251113_064143 API usage tracker"""
    
    # API pricing (per 1000 calls)
    API_PRICE_CENTS_PER_1K = 5  # $0.05 per 1K API calls
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics = metrics_collector
        self.events = event_logger
    
    async def track_api_call(
        self,
        tenant_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        api_key_id: Optional[str] = None
    ):
        """DELTA:20251113_064143 Track API call"""
        # Calculate cost (only charge for successful calls)
        cost_cents = 0
        if status_code < 400:
            cost_cents = int(self.API_PRICE_CENTS_PER_1K / 1000)  # Per call
        
        query = """
            INSERT INTO api_usage (
                tenant_id, api_key_id, endpoint, method, status_code, response_time_ms, cost_cents
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7);
        """
        
        await self.postgres_conn.execute(
            query,
            tenant_id, api_key_id, endpoint, method, status_code, response_time_ms, cost_cents
        )
        
        # Record metrics
        self.metrics.increment_counter(
            'api_calls_total',
            tags={
                'endpoint': endpoint,
                'method': method,
                'status_code': str(status_code)
            }
        )
        
        self.metrics.record_histogram(
            'api_response_time_ms',
            value=response_time_ms,
            tags={'endpoint': endpoint}
        )
    
    async def get_usage_summary(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """DELTA:20251113_064143 Get API usage summary"""
        if start_date and end_date:
            query = """
                SELECT 
                    COUNT(*) as total_calls,
                    COUNT(*) FILTER (WHERE status_code < 400) as successful_calls,
                    COUNT(*) FILTER (WHERE status_code >= 400) as failed_calls,
                    SUM(cost_cents) as total_cost_cents,
                    AVG(response_time_ms) as avg_response_time_ms,
                    COUNT(DISTINCT endpoint) as unique_endpoints
                FROM api_usage
                WHERE tenant_id = $1::uuid
                  AND created_at >= $2
                  AND created_at <= $3;
            """
            row = await self.postgres_conn.fetchrow(query, tenant_id, start_date, end_date)
        else:
            query = """
                SELECT 
                    COUNT(*) as total_calls,
                    COUNT(*) FILTER (WHERE status_code < 400) as successful_calls,
                    COUNT(*) FILTER (WHERE status_code >= 400) as failed_calls,
                    SUM(cost_cents) as total_cost_cents,
                    AVG(response_time_ms) as avg_response_time_ms,
                    COUNT(DISTINCT endpoint) as unique_endpoints
                FROM api_usage
                WHERE tenant_id = $1::uuid;
            """
            row = await self.postgres_conn.fetchrow(query, tenant_id)
        
        if not row or row['total_calls'] is None:
            return {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_cost_cents': 0,
                'avg_response_time_ms': 0,
                'unique_endpoints': 0
            }
        
        return {
            'total_calls': row['total_calls'],
            'successful_calls': row['successful_calls'] or 0,
            'failed_calls': row['failed_calls'] or 0,
            'total_cost_cents': row['total_cost_cents'] or 0,
            'avg_response_time_ms': float(row['avg_response_time_ms'] or 0),
            'unique_endpoints': row['unique_endpoints'] or 0
        }
    
    async def check_rate_limit(
        self,
        tenant_id: str,
        limit_per_hour: int = 1000
    ) -> Dict[str, Any]:
        """DELTA:20251113_064143 Check if tenant has exceeded rate limit"""
        query = """
            SELECT COUNT(*) as calls_last_hour
            FROM api_usage
            WHERE tenant_id = $1::uuid
              AND created_at >= NOW() - INTERVAL '1 hour';
        """
        
        row = await self.postgres_conn.fetchrow(query, tenant_id)
        calls_last_hour = row['calls_last_hour'] or 0
        
        return {
            'calls_last_hour': calls_last_hour,
            'limit_per_hour': limit_per_hour,
            'remaining': max(0, limit_per_hour - calls_last_hour),
            'exceeded': calls_last_hour >= limit_per_hour
        }
