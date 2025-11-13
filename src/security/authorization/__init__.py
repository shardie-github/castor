"""
Advanced Authorization Module

Provides RBAC, ABAC, and permission management.
"""

from src.security.authorization.rbac import RBACManager, Role, Permission
from src.security.authorization.abac import ABACManager, AccessControlPolicy
from src.security.authorization.permission_engine import PermissionEngine

__all__ = [
    "RBACManager",
    "Role",
    "Permission",
    "ABACManager",
    "AccessControlPolicy",
    "PermissionEngine",
]
