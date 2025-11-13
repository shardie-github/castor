"""
Attribute-Based Access Control (ABAC)

Implements ABAC for fine-grained, context-aware access control.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from uuid import uuid4
from dataclasses import dataclass

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


@dataclass
class AccessControlPolicy:
    """Access control policy data structure"""
    policy_id: str
    tenant_id: str
    policy_name: str
    policy_type: str  # 'rbac', 'abac', 'hybrid'
    resource_type: str
    action: str
    conditions: Dict[str, Any]
    effect: str  # 'allow' or 'deny'
    priority: int
    enabled: bool


class ABACManager:
    """
    Attribute-Based Access Control Manager
    
    Manages ABAC policies for context-aware access control.
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
    
    async def create_policy(
        self,
        tenant_id: str,
        policy_name: str,
        resource_type: str,
        action: str,
        conditions: Dict[str, Any],
        effect: str = "allow",
        policy_type: str = "abac",
        priority: int = 100
    ) -> AccessControlPolicy:
        """Create an access control policy"""
        policy_id = str(uuid4())
        
        await self.postgres.execute(
            """
            INSERT INTO access_control_policies (
                policy_id, tenant_id, policy_name, policy_type, resource_type,
                action, conditions, effect, priority
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            policy_id, tenant_id, policy_name, policy_type, resource_type,
            action, conditions, effect, priority
        )
        
        return AccessControlPolicy(
            policy_id=policy_id,
            tenant_id=tenant_id,
            policy_name=policy_name,
            policy_type=policy_type,
            resource_type=resource_type,
            action=action,
            conditions=conditions,
            effect=effect,
            priority=priority,
            enabled=True
        )
    
    async def evaluate_access(
        self,
        tenant_id: str,
        user_id: str,
        resource_type: str,
        action: str,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate access using ABAC policies
        
        Returns:
            Dictionary with 'allowed' boolean and 'reason'
        """
        context = context or {}
        
        # Get applicable policies (ordered by priority)
        policies = await self.postgres.fetch(
            """
            SELECT policy_id, policy_name, conditions, effect, priority
            FROM access_control_policies
            WHERE tenant_id = $1 AND resource_type = $2 AND action = $3
            AND enabled = TRUE
            ORDER BY priority DESC
            """,
            tenant_id, resource_type, action
        )
        
        # Evaluate policies in priority order
        for policy_row in policies:
            conditions = policy_row["conditions"] or {}
            effect = policy_row["effect"]
            
            # Evaluate conditions
            if self._evaluate_conditions(conditions, user_id, resource_id, context):
                # Log access decision
                await self._log_access_decision(
                    tenant_id, user_id, resource_type, resource_id, action,
                    True, policy_row["policy_id"], f"Policy: {policy_row['policy_name']}"
                )
                
                return {
                    "allowed": effect == "allow",
                    "reason": f"Policy: {policy_row['policy_name']}",
                    "policy_id": str(policy_row["policy_id"])
                }
        
        # Default deny if no policy matches
        await self._log_access_decision(
            tenant_id, user_id, resource_type, resource_id, action,
            False, None, "No matching policy"
        )
        
        return {
            "allowed": False,
            "reason": "No matching policy"
        }
    
    async def set_resource_owner(
        self,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        owner_id: str,
        owner_type: str = "user"
    ) -> bool:
        """Set resource owner (for ownership-based access)"""
        await self.postgres.execute(
            """
            INSERT INTO resource_ownership (
                ownership_id, tenant_id, resource_type, resource_id,
                owner_id, owner_type
            )
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5)
            ON CONFLICT (tenant_id, resource_type, resource_id)
            DO UPDATE SET owner_id = $4, owner_type = $5
            """,
            tenant_id, resource_type, resource_id, owner_id, owner_type
        )
        
        return True
    
    async def get_resource_owner(
        self,
        tenant_id: str,
        resource_type: str,
        resource_id: str
    ) -> Optional[str]:
        """Get resource owner"""
        row = await self.postgres.fetchrow(
            """
            SELECT owner_id
            FROM resource_ownership
            WHERE tenant_id = $1 AND resource_type = $2 AND resource_id = $3
            """,
            tenant_id, resource_type, resource_id
        )
        
        return str(row["owner_id"]) if row else None
    
    def _evaluate_conditions(
        self,
        conditions: Dict[str, Any],
        user_id: str,
        resource_id: Optional[str],
        context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate ABAC conditions
        
        Supports conditions like:
        - user.role == 'admin'
        - resource.owner == user.id
        - time.hour >= 9 AND time.hour <= 17
        - ip_address IN ['192.168.1.0/24']
        """
        if not conditions:
            return True
        
        # Evaluate each condition
        for key, value in conditions.items():
            if key == "user.role":
                # Check user role (simplified)
                if not self._check_user_role(user_id, value):
                    return False
            
            elif key == "resource.owner":
                # Check resource ownership
                if resource_id and not self._check_resource_owner(resource_id, user_id):
                    return False
            
            elif key == "time.hour":
                # Check time conditions
                current_hour = datetime.now(timezone.utc).hour
                if isinstance(value, dict):
                    if "gte" in value and current_hour < value["gte"]:
                        return False
                    if "lte" in value and current_hour > value["lte"]:
                        return False
                elif current_hour != value:
                    return False
            
            elif key == "ip_address":
                # Check IP address (simplified)
                ip = context.get("ip_address")
                if ip and not self._check_ip_address(ip, value):
                    return False
        
        return True
    
    def _check_user_role(self, user_id: str, role: str) -> bool:
        """Check if user has role (simplified - in production, query database)"""
        # In production, query user_roles table
        return False
    
    def _check_resource_owner(self, resource_id: str, user_id: str) -> bool:
        """Check if user owns resource (simplified)"""
        # In production, query resource_ownership table
        return False
    
    def _check_ip_address(self, ip: str, allowed_ips: List[str]) -> bool:
        """Check if IP is in allowed list (simplified)"""
        # In production, implement CIDR matching
        return ip in allowed_ips
    
    async def _log_access_decision(
        self,
        tenant_id: str,
        user_id: str,
        resource_type: str,
        resource_id: Optional[str],
        action: str,
        allowed: bool,
        policy_id: Optional[str],
        reason: str
    ):
        """Log access decision for audit"""
        await self.postgres.execute(
            """
            INSERT INTO access_logs (
                log_id, tenant_id, user_id, resource_type, resource_id,
                action, allowed, policy_applied, decision_reason
            )
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, $8)
            """,
            tenant_id, user_id, resource_type, resource_id, action,
            allowed, policy_id, reason
        )
