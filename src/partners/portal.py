"""
Partner Portal

Provides partner dashboard, documentation, and support resources.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.partners.referral import ReferralProgram
from src.partners.marketplace import MarketplaceManager

logger = logging.getLogger(__name__)


class PartnerPortal:
    """Partner portal providing dashboard and resources"""
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        referral_program: ReferralProgram,
        marketplace_manager: MarketplaceManager,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.referral_program = referral_program
        self.marketplace_manager = marketplace_manager
        self.metrics_collector = metrics_collector
        self.event_logger = event_logger
    
    async def get_partner_dashboard(self, partner_id: str) -> Dict:
        """Get partner dashboard data"""
        # Get referral stats
        referral_stats = await self.referral_program.get_referral_stats(partner_id)
        
        # Get marketplace stats (if partner has listings)
        marketplace_stats = await self.marketplace_manager.get_marketplace_stats()
        
        # Get recent activity
        recent_referrals = await self.referral_program.list_referrals(
            referrer_id=partner_id,
            limit=10
        )
        
        return {
            "partner_id": partner_id,
            "referral_stats": referral_stats,
            "marketplace_stats": marketplace_stats,
            "recent_referrals": [
                {
                    "referral_id": r.referral_id,
                    "referral_code": r.referral_code,
                    "status": r.status.value,
                    "total_commission_earned": r.total_commission_earned,
                    "created_at": r.created_at.isoformat()
                }
                for r in recent_referrals
            ],
            "resources": {
                "api_documentation": "https://docs.example.com/api",
                "marketing_materials": "https://partners.example.com/materials",
                "support": "https://partners.example.com/support",
                "integration_guides": "https://docs.example.com/integrations"
            }
        }
    
    async def get_integration_documentation(self, integration_type: str) -> Dict:
        """Get integration documentation"""
        # In production, this would fetch from documentation system
        return {
            "integration_type": integration_type,
            "documentation_url": f"https://docs.example.com/integrations/{integration_type}",
            "api_endpoints": [
                f"/api/v1/integrations/{integration_type}/connect",
                f"/api/v1/integrations/{integration_type}/webhook"
            ],
            "example_code": {
                "python": f"# Example Python code for {integration_type}",
                "javascript": f"// Example JavaScript code for {integration_type}"
            }
        }
    
    async def get_marketing_materials(self) -> Dict:
        """Get marketing materials for partners"""
        return {
            "logos": {
                "primary": "https://partners.example.com/assets/logo-primary.png",
                "secondary": "https://partners.example.com/assets/logo-secondary.png",
                "icon": "https://partners.example.com/assets/icon.png"
            },
            "screenshots": [
                "https://partners.example.com/assets/screenshot1.png",
                "https://partners.example.com/assets/screenshot2.png"
            ],
            "case_studies": [
                "https://partners.example.com/case-studies/case1.pdf",
                "https://partners.example.com/case-studies/case2.pdf"
            ],
            "co_marketing_templates": [
                "https://partners.example.com/templates/email-template.html",
                "https://partners.example.com/templates/social-media-template.html"
            ]
        }
