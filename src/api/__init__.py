"""
API Routes Module

All API route modules are imported here for easy access.
"""

# Core API routes
from src.api import tenants, attribution, ai, cost, security, backup, optimization, risk, partners, business

# Authentication, billing, and campaigns
from src.api import auth, billing, campaigns

# Feature-flagged routes (imported conditionally in main.py)
# etl, match, io, deals, dashboard, automation, monetization, orchestration

__all__ = [
    "tenants",
    "attribution",
    "ai",
    "cost",
    "security",
    "backup",
    "optimization",
    "risk",
    "partners",
    "business",
    "auth",
    "billing",
    "campaigns",
]
