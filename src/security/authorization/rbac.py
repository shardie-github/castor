"""
Role-Based Access Control (RBAC)

Implements RBAC for fine-grained permission management.
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
class Role:
    """Role data structure"""
    role_id: str
    tenant_id: str
    role_name: str
    role_type: str  # 'system' or 'custom'
    description: Optional[str]
    permissions: List[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class Permission:
    """Permission data structure"""
    permission_id: str
    tenant_id: str
    permission_name: str
    resource_type: str
    action: str
    description: Optional[str]
    conditions: Dict[str, Any]


class RBACManager:
    """
    Role-Based Access Control Manager
    
    Manages roles, permissions, and user-role assignments.
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
    
    async def create_role(
        self,
        tenant_id: str,
        role_name: str,
        description: Optional[str] = None,
        role_type: str = "custom",
        permissions: Optional[List[str]] = None
    ) -> Role:
        """Create a new role"""
        role_id = str(uuid4())
        
        await self.postgres.execute(
            """
            INSERT INTO roles (
                role_id, tenant_id, role_name, role_type, description, permissions
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            role_id, tenant_id, role_name, role_type, description, permissions or []
        )
        
        # Log event
        await self.events.log_event(
            event_type="role_created",
            user_id=None,
            properties={
                "role_id": role_id,
                "role_name": role_name,
                "tenant_id": tenant_id
            }
        )
        
        return Role(
            role_id=role_id,
            tenant_id=tenant_id,
            role_name=role_name,
            role_type=role_type,
            description=description,
            permissions=permissions or [],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    async def get_role(self, tenant_id: str, role_id: str) -> Optional[Role]:
        """Get role by ID"""
        row = await self.postgres.fetchrow(
            """
            SELECT role_id, tenant_id, role_name, role_type, description,
                   permissions, created_at, updated_at
            FROM roles
            WHERE tenant_id = $1 AND role_id = $2
            """,
            tenant_id, role_id
        )
        
        if not row:
            return None
        
        return Role(
            role_id=str(row["role_id"]),
            tenant_id=str(row["tenant_id"]),
            role_name=row["role_name"],
            role_type=row["role_type"],
            description=row["description"],
            permissions=row["permissions"] or [],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
    
    async def assign_role_to_user(
        self,
        tenant_id: str,
        user_id: str,
        role_id: str,
        assigned_by: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Assign role to user"""
        await self.postgres.execute(
            """
            INSERT INTO user_roles (
                user_role_id, tenant_id, user_id, role_id, assigned_by, expires_at
            )
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5)
            ON CONFLICT (tenant_id, user_id, role_id) DO NOTHING
            """,
            tenant_id, user_id, role_id, assigned_by, expires_at
        )
        
        # Log event
        await self.events.log_event(
            event_type="role_assigned",
            user_id=assigned_by,
            properties={
                "user_id": user_id,
                "role_id": role_id,
                "tenant_id": tenant_id
            }
        )
        
        return True
    
    async def revoke_role_from_user(
        self,
        tenant_id: str,
        user_id: str,
        role_id: str
    ) -> bool:
        """Revoke role from user"""
        await self.postgres.execute(
            """
            DELETE FROM user_roles
            WHERE tenant_id = $1 AND user_id = $2 AND role_id = $3
            """,
            tenant_id, user_id, role_id
        )
        
        # Log event
        await self.events.log_event(
            event_type="role_revoked",
            user_id=None,
            properties={
                "user_id": user_id,
                "role_id": role_id,
                "tenant_id": tenant_id
            }
        )
        
        return True
    
    async def get_user_roles(
        self,
        tenant_id: str,
        user_id: str
    ) -> List[Role]:
        """Get all roles for a user"""
        rows = await self.postgres.fetch(
            """
            SELECT r.role_id, r.tenant_id, r.role_name, r.role_type, r.description,
                   r.permissions, r.created_at, r.updated_at
            FROM roles r
            INNER JOIN user_roles ur ON r.role_id = ur.role_id
            WHERE ur.tenant_id = $1 AND ur.user_id = $2
            AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
            """,
            tenant_id, user_id
        )
        
        return [
            Role(
                role_id=str(row["role_id"]),
                tenant_id=str(row["tenant_id"]),
                role_name=row["role_name"],
                role_type=row["role_type"],
                description=row["description"],
                permissions=row["permissions"] or [],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]
    
    async def create_permission(
        self,
        tenant_id: str,
        permission_name: str,
        resource_type: str,
        action: str,
        description: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None
    ) -> Permission:
        """Create a new permission"""
        permission_id = str(uuid4())
        
        await self.postgres.execute(
            """
            INSERT INTO permissions (
                permission_id, tenant_id, permission_name, resource_type,
                action, description, conditions
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            permission_id, tenant_id, permission_name, resource_type,
            action, description, conditions or {}
        )
        
        return Permission(
            permission_id=permission_id,
            tenant_id=tenant_id,
            permission_name=permission_name,
            resource_type=resource_type,
            action=action,
            description=description,
            conditions=conditions or {}
        )
    
    async def assign_permission_to_role(
        self,
        tenant_id: str,
        role_id: str,
        permission_id: str,
        conditions: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Assign permission to role"""
        await self.postgres.execute(
            """
            INSERT INTO role_permissions (
                role_permission_id, tenant_id, role_id, permission_id, conditions
            )
            VALUES (gen_random_uuid(), $1, $2, $3, $4)
            ON CONFLICT (tenant_id, role_id, permission_id) DO NOTHING
            """,
            tenant_id, role_id, permission_id, conditions or {}
        )
        
        return True
    
    async def check_permission(
        self,
        tenant_id: str,
        user_id: str,
        resource_type: str,
        action: str,
        resource_id: Optional[str] = None
    ) -> bool:
        """
        Check if user has permission to perform action on resource
        
        Returns:
            True if user has permission, False otherwise
        """
        # Get user roles
        roles = await self.get_user_roles(tenant_id, user_id)
        
        # Check each role for permission
        for role in roles:
            # Check role permissions
            permission_rows = await self.postgres.fetch(
                """
                SELECT p.permission_id, p.resource_type, p.action, rp.conditions
                FROM permissions p
                INNER JOIN role_permissions rp ON p.permission_id = rp.permission_id
                WHERE rp.tenant_id = $1 AND rp.role_id = $2
                AND p.resource_type = $3 AND p.action = $4
                """,
                tenant_id, role.role_id, resource_type, action
            )
            
            if permission_rows:
                # Check conditions if any
                for perm_row in permission_rows:
                    conditions = perm_row["conditions"] or {}
                    
                    # Evaluate conditions (simplified - in production, use proper condition evaluator)
                    if self._evaluate_conditions(conditions, resource_id):
                        return True
        
        return False
    
    def _evaluate_conditions(
        self,
        conditions: Dict[str, Any],
        resource_id: Optional[str]
    ) -> bool:
        """Evaluate permission conditions"""
        # In production, implement proper condition evaluation
        # For now, return True if no conditions
        return len(conditions) == 0
