"""
DELTA:20251113_064143 White Label Manager

Manages white-labeling settings for tenants.
"""

import logging
from typing import Optional, Dict, Any

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class WhiteLabelManager:
    """DELTA:20251113_064143 White label manager"""
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics = metrics_collector
        self.events = event_logger
    
    async def get_settings(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """DELTA:20251113_064143 Get white label settings"""
        query = """
            SELECT setting_id, tenant_id, brand_name, logo_url, primary_color, secondary_color,
                   custom_domain, custom_css, email_from_name, email_from_address,
                   support_email, support_url, enabled, created_at, updated_at
            FROM white_label_settings
            WHERE tenant_id = $1::uuid;
        """
        
        row = await self.postgres_conn.fetchrow(query, tenant_id)
        
        if not row:
            return None
        
        return {
            'setting_id': str(row['setting_id']),
            'tenant_id': str(row['tenant_id']),
            'brand_name': row['brand_name'],
            'logo_url': row['logo_url'],
            'primary_color': row['primary_color'],
            'secondary_color': row['secondary_color'],
            'custom_domain': row['custom_domain'],
            'custom_css': row['custom_css'],
            'email_from_name': row['email_from_name'],
            'email_from_address': row['email_from_address'],
            'support_email': row['support_email'],
            'support_url': row['support_url'],
            'enabled': row['enabled'],
            'created_at': row['created_at'].isoformat(),
            'updated_at': row['updated_at'].isoformat()
        }
    
    async def update_settings(
        self,
        tenant_id: str,
        brand_name: Optional[str] = None,
        logo_url: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
        custom_domain: Optional[str] = None,
        custom_css: Optional[str] = None,
        email_from_name: Optional[str] = None,
        email_from_address: Optional[str] = None,
        support_email: Optional[str] = None,
        support_url: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> Dict[str, Any]:
        """DELTA:20251113_064143 Update white label settings"""
        # Build update query dynamically
        updates = []
        params = []
        param_idx = 1
        
        if brand_name is not None:
            updates.append(f"brand_name = ${param_idx}")
            params.append(brand_name)
            param_idx += 1
        
        if logo_url is not None:
            updates.append(f"logo_url = ${param_idx}")
            params.append(logo_url)
            param_idx += 1
        
        if primary_color is not None:
            updates.append(f"primary_color = ${param_idx}")
            params.append(primary_color)
            param_idx += 1
        
        if secondary_color is not None:
            updates.append(f"secondary_color = ${param_idx}")
            params.append(secondary_color)
            param_idx += 1
        
        if custom_domain is not None:
            updates.append(f"custom_domain = ${param_idx}")
            params.append(custom_domain)
            param_idx += 1
        
        if custom_css is not None:
            updates.append(f"custom_css = ${param_idx}")
            params.append(custom_css)
            param_idx += 1
        
        if email_from_name is not None:
            updates.append(f"email_from_name = ${param_idx}")
            params.append(email_from_name)
            param_idx += 1
        
        if email_from_address is not None:
            updates.append(f"email_from_address = ${param_idx}")
            params.append(email_from_address)
            param_idx += 1
        
        if support_email is not None:
            updates.append(f"support_email = ${param_idx}")
            params.append(support_email)
            param_idx += 1
        
        if support_url is not None:
            updates.append(f"support_url = ${param_idx}")
            params.append(support_url)
            param_idx += 1
        
        if enabled is not None:
            updates.append(f"enabled = ${param_idx}")
            params.append(enabled)
            param_idx += 1
        
        if not updates:
            return await self.get_settings(tenant_id) or {}
        
        updates.append(f"updated_at = NOW()")
        params.append(tenant_id)
        
        query = f"""
            INSERT INTO white_label_settings (tenant_id, {', '.join([u.split(' = ')[0] for u in updates if 'updated_at' not in u])})
            VALUES (${param_idx}::uuid, {', '.join([f'${i}' for i in range(1, param_idx)])})
            ON CONFLICT (tenant_id) DO UPDATE
            SET {', '.join(updates)}
            RETURNING setting_id;
        """
        
        # Simplified approach - use upsert
        upsert_query = """
            INSERT INTO white_label_settings (
                tenant_id, brand_name, logo_url, primary_color, secondary_color,
                custom_domain, custom_css, email_from_name, email_from_address,
                support_email, support_url, enabled, updated_at
            )
            VALUES (
                $1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW()
            )
            ON CONFLICT (tenant_id) DO UPDATE
            SET brand_name = COALESCE(EXCLUDED.brand_name, white_label_settings.brand_name),
                logo_url = COALESCE(EXCLUDED.logo_url, white_label_settings.logo_url),
                primary_color = COALESCE(EXCLUDED.primary_color, white_label_settings.primary_color),
                secondary_color = COALESCE(EXCLUDED.secondary_color, white_label_settings.secondary_color),
                custom_domain = COALESCE(EXCLUDED.custom_domain, white_label_settings.custom_domain),
                custom_css = COALESCE(EXCLUDED.custom_css, white_label_settings.custom_css),
                email_from_name = COALESCE(EXCLUDED.email_from_name, white_label_settings.email_from_name),
                email_from_address = COALESCE(EXCLUDED.email_from_address, white_label_settings.email_from_address),
                support_email = COALESCE(EXCLUDED.support_email, white_label_settings.support_email),
                support_url = COALESCE(EXCLUDED.support_url, white_label_settings.support_url),
                enabled = COALESCE(EXCLUDED.enabled, white_label_settings.enabled),
                updated_at = NOW()
            RETURNING setting_id;
        """
        
        await self.postgres_conn.execute(
            upsert_query,
            tenant_id, brand_name, logo_url, primary_color, secondary_color,
            custom_domain, custom_css, email_from_name, email_from_address,
            support_email, support_url, enabled
        )
        
        await self.events.log_event(
            event_type='white_label.updated',
            user_id=None,
            properties={
                'tenant_id': tenant_id,
                'enabled': enabled
            }
        )
        
        return await self.get_settings(tenant_id) or {}
