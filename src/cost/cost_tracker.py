"""
Cost Tracker

Tracks resource usage and costs per tenant.
"""

import logging
from datetime import datetime, timezone, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class CostType(Enum):
    """Cost types"""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    API_CALLS = "api_calls"
    DATABASE = "database"
    CACHE = "cache"
    OTHER = "other"


@dataclass
class CostAllocation:
    """Cost allocation record"""
    allocation_id: str
    tenant_id: str
    date: date
    cost_type: CostType
    service_name: str
    amount: float
    currency: str = "USD"
    metadata: Dict[str, Any] = None


class CostTracker:
    """
    Cost Tracker
    
    Tracks resource usage and allocates costs to tenants.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        postgres_conn: PostgresConnection
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.postgres = postgres_conn
    
    async def track_resource_usage(
        self,
        tenant_id: str,
        resource_type: str,
        metric_name: str,
        metric_value: float,
        resource_id: Optional[str] = None,
        unit: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track resource usage"""
        await self.postgres.execute(
            """
            INSERT INTO resource_usage (
                usage_id, tenant_id, timestamp, resource_type, resource_id,
                metric_name, metric_value, unit, metadata
            )
            VALUES (gen_random_uuid(), $1, NOW(), $2, $3, $4, $5, $6, $7)
            """,
            tenant_id, resource_type, resource_id, metric_name, metric_value, unit, metadata or {}
        )
        
        # Record telemetry
        self.metrics.increment_counter(
            "resource_usage_tracked",
            tags={"tenant_id": tenant_id, "resource_type": resource_type}
        )
    
    async def allocate_cost(
        self,
        tenant_id: str,
        cost_type: CostType,
        service_name: str,
        amount: float,
        date: Optional[date] = None,
        resource_id: Optional[str] = None,
        currency: str = "USD",
        unit: Optional[str] = None,
        quantity: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Allocate cost to tenant"""
        if date is None:
            date = datetime.now(timezone.utc).date()
        
        await self.postgres.execute(
            """
            INSERT INTO cost_allocations (
                allocation_id, tenant_id, date, cost_type, service_name,
                resource_id, amount, currency, unit, quantity, metadata
            )
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            tenant_id, date, cost_type.value, service_name, resource_id,
            amount, currency, unit, quantity, metadata or {}
        )
        
        # Record telemetry
        self.metrics.increment_counter(
            "cost_allocated",
            tags={"tenant_id": tenant_id, "cost_type": cost_type.value}
        )
    
    async def get_tenant_costs(
        self,
        tenant_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[CostAllocation]:
        """Get costs for tenant"""
        query = """
            SELECT allocation_id, tenant_id, date, cost_type, service_name,
                   amount, currency, metadata
            FROM cost_allocations
            WHERE tenant_id = $1
        """
        
        params = [tenant_id]
        if start_date:
            query += " AND date >= $" + str(len(params) + 1)
            params.append(start_date)
        if end_date:
            query += " AND date <= $" + str(len(params) + 1)
            params.append(end_date)
        
        query += " ORDER BY date DESC"
        
        rows = await self.postgres.fetch(query, *params)
        
        return [
            CostAllocation(
                allocation_id=str(row["allocation_id"]),
                tenant_id=str(row["tenant_id"]),
                date=row["date"],
                cost_type=CostType(row["cost_type"]),
                service_name=row["service_name"],
                amount=float(row["amount"]),
                currency=row["currency"],
                metadata=row["metadata"] or {}
            )
            for row in rows
        ]
    
    async def get_total_cost(
        self,
        tenant_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> float:
        """Get total cost for tenant"""
        query = """
            SELECT SUM(amount) as total
            FROM cost_allocations
            WHERE tenant_id = $1
        """
        
        params = [tenant_id]
        if start_date:
            query += " AND date >= $" + str(len(params) + 1)
            params.append(start_date)
        if end_date:
            query += " AND date <= $" + str(len(params) + 1)
            params.append(end_date)
        
        result = await self.postgres.fetchval(query, *params)
        return float(result) if result else 0.0
