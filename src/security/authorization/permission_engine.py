"""
Permission Engine

Unified permission evaluation engine combining RBAC and ABAC.
"""

import logging
from typing import Dict, Optional, Any

from src.security.authorization.rbac import RBACManager
from src.security.authorization.abac import ABACManager
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class PermissionEngine:
    """
    Permission Engine
    
    Unified engine for evaluating permissions using both RBAC and ABAC.
    """
    
    def __init__(
        self,
        rbac_manager: RBACManager,
        abac_manager: ABACManager,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.rbac = rbac_manager
        self.abac = abac_manager
        self.metrics = metrics_collector
        self.events = event_logger
    
    async def check_permission(
        self,
        tenant_id: str,
        user_id: str,
        resource_type: str,
        action: str,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if user has permission (combines RBAC and ABAC)
        
        Returns:
            True if user has permission, False otherwise
        """
        # First check RBAC
        rbac_allowed = await self.rbac.check_permission(
            tenant_id, user_id, resource_type, action, resource_id
        )
        
        if not rbac_allowed:
            return False
        
        # Then check ABAC policies
        abac_result = await self.abac.evaluate_access(
            tenant_id, user_id, resource_type, action, resource_id, context
        )
        
        return abac_result["allowed"]
    
    async def check_resource_access(
        self,
        tenant_id: str,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check resource access with detailed result
        
        Returns:
            Dictionary with access decision and details
        """
        # Check RBAC
        rbac_allowed = await self.rbac.check_permission(
            tenant_id, user_id, resource_type, action, resource_id
        )
        
        if not rbac_allowed:
            return {
                "allowed": False,
                "reason": "RBAC check failed",
                "rbac_allowed": False,
                "abac_allowed": None
            }
        
        # Check ABAC
        abac_result = await self.abac.evaluate_access(
            tenant_id, user_id, resource_type, action, resource_id, context
        )
        
        return {
            "allowed": abac_result["allowed"],
            "reason": abac_result.get("reason"),
            "rbac_allowed": True,
            "abac_allowed": abac_result["allowed"],
            "policy_id": abac_result.get("policy_id")
        }
