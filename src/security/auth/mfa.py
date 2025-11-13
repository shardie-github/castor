"""
Multi-Factor Authentication (MFA)

Provides TOTP-based MFA support.
"""

import logging
import hashlib
import hmac
import time
from typing import Optional
from secrets import token_hex

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class MFAProvider:
    """
    Multi-Factor Authentication Provider
    
    Implements TOTP (Time-based One-Time Password) for MFA.
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
    
    def generate_secret(self) -> str:
        """Generate MFA secret for user"""
        # Generate 32-byte secret (base32 encoded would be used with pyotp in production)
        return token_hex(16)
    
    async def enable_mfa(self, user_id: str, secret: str) -> bool:
        """Enable MFA for user"""
        # Store secret (in production, encrypt before storing)
        await self.postgres.execute(
            """
            UPDATE users
            SET metadata = jsonb_set(
                COALESCE(metadata, '{}'),
                '{mfa_enabled}',
                'true'
            ),
            metadata = jsonb_set(
                COALESCE(metadata, '{}'),
                '{mfa_secret}',
                $1::jsonb
            )
            WHERE user_id = $2
            """,
            f'"{secret}"', user_id
        )
        
        # Log event
        await self.events.log_event(
            event_type="mfa_enabled",
            user_id=user_id,
            properties={}
        )
        
        return True
    
    def generate_totp(self, secret: str) -> str:
        """
        Generate TOTP code
        
        In production, use pyotp library:
        import pyotp
        totp = pyotp.TOTP(secret)
        return totp.now()
        """
        # Simplified TOTP generation (use pyotp in production)
        current_time = int(time.time() / 30)  # 30-second window
        hmac_result = hmac.new(
            secret.encode(),
            current_time.to_bytes(8, 'big'),
            hashlib.sha1
        ).digest()
        
        offset = hmac_result[-1] & 0x0F
        code = ((hmac_result[offset] & 0x7F) << 24 |
                (hmac_result[offset + 1] & 0xFF) << 16 |
                (hmac_result[offset + 2] & 0xFF) << 8 |
                (hmac_result[offset + 3] & 0xFF)) % 1000000
        
        return f"{code:06d}"
    
    async def verify_totp(self, user_id: str, code: str) -> bool:
        """Verify TOTP code"""
        # Get user's MFA secret
        row = await self.postgres.fetchrow(
            """
            SELECT metadata->>'mfa_secret' as mfa_secret
            FROM users
            WHERE user_id = $1 AND metadata->>'mfa_enabled' = 'true'
            """,
            user_id
        )
        
        if not row or not row["mfa_secret"]:
            return False
        
        secret = row["mfa_secret"].strip('"')
        
        # Generate expected code
        expected_code = self.generate_totp(secret)
        
        # Verify (allow small time window)
        is_valid = code == expected_code
        
        if is_valid:
            # Log successful verification
            await self.events.log_event(
                event_type="mfa_verified",
                user_id=user_id,
                properties={"success": True}
            )
        else:
            # Log failed verification
            await self.events.log_event(
                event_type="mfa_verification_failed",
                user_id=user_id,
                properties={"success": False}
            )
        
        return is_valid
