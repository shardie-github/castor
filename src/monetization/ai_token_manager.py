"""
DELTA:20251113_064143 AI Token Manager

Manages AI token purchases, usage tracking, and billing.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class AITokenManager:
    """DELTA:20251113_064143 AI token manager"""
    
    # Token pricing (per 1000 tokens)
    TOKEN_PRICE_CENTS_PER_1K = 10  # $0.10 per 1K tokens
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics = metrics_collector
        self.events = event_logger
    
    async def purchase_tokens(
        self,
        tenant_id: str,
        tokens_to_purchase: int,
        transaction_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """DELTA:20251113_064143 Purchase AI tokens"""
        cost_cents = int((tokens_to_purchase / 1000) * self.TOKEN_PRICE_CENTS_PER_1K)
        
        # Get or create balance
        query = """
            INSERT INTO ai_token_balances (tenant_id, tokens_purchased, tokens_remaining, last_purchase_at)
            VALUES ($1::uuid, $2, $2, NOW())
            ON CONFLICT (tenant_id) DO UPDATE
            SET tokens_purchased = ai_token_balances.tokens_purchased + $2,
                tokens_remaining = ai_token_balances.tokens_remaining + $2,
                last_purchase_at = NOW(),
                updated_at = NOW()
            RETURNING tokens_remaining, tokens_purchased;
        """
        
        row = await self.postgres_conn.fetchrow(query, tenant_id, tokens_to_purchase)
        
        # Record transaction
        if transaction_id:
            await self._record_transaction(
                tenant_id=tenant_id,
                transaction_type='ai_tokens',
                amount_cents=cost_cents,
                external_transaction_id=transaction_id,
                description=f"Purchased {tokens_to_purchase} AI tokens"
            )
        
        await self.events.log_event(
            event_type='ai_tokens.purchased',
            user_id=None,
            properties={
                'tenant_id': tenant_id,
                'tokens_purchased': tokens_to_purchase,
                'cost_cents': cost_cents
            }
        )
        
        return {
            'tokens_purchased': tokens_to_purchase,
            'tokens_remaining': row['tokens_remaining'],
            'total_purchased': row['tokens_purchased'],
            'cost_cents': cost_cents
        }
    
    async def use_tokens(
        self,
        tenant_id: str,
        tokens_used: int,
        feature_type: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """DELTA:20251113_064143 Use AI tokens"""
        # Check balance
        balance = await self.get_balance(tenant_id)
        
        if balance['tokens_remaining'] < tokens_used:
            raise ValueError(f"Insufficient tokens. Available: {balance['tokens_remaining']}, Required: {tokens_used}")
        
        # Calculate cost
        cost_cents = int((tokens_used / 1000) * self.TOKEN_PRICE_CENTS_PER_1K)
        
        # Deduct tokens
        update_query = """
            UPDATE ai_token_balances
            SET tokens_used = tokens_used + $1,
                tokens_remaining = tokens_remaining - $1,
                last_usage_at = NOW(),
                updated_at = NOW()
            WHERE tenant_id = $2::uuid;
        """
        
        await self.postgres_conn.execute(update_query, tokens_used, tenant_id)
        
        # Record usage
        usage_query = """
            INSERT INTO ai_token_usage (
                tenant_id, user_id, feature_type, tokens_used, cost_cents, request_id
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6);
        """
        
        await self.postgres_conn.execute(
            usage_query,
            tenant_id, user_id, feature_type, tokens_used, cost_cents, request_id
        )
        
        await self.events.log_event(
            event_type='ai_tokens.used',
            user_id=user_id,
            properties={
                'tenant_id': tenant_id,
                'tokens_used': tokens_used,
                'feature_type': feature_type,
                'cost_cents': cost_cents
            }
        )
        
        return {
            'tokens_used': tokens_used,
            'cost_cents': cost_cents,
            'tokens_remaining': balance['tokens_remaining'] - tokens_used
        }
    
    async def get_balance(self, tenant_id: str) -> Dict[str, Any]:
        """DELTA:20251113_064143 Get token balance"""
        query = """
            SELECT tokens_purchased, tokens_used, tokens_remaining,
                   last_purchase_at, last_usage_at
            FROM ai_token_balances
            WHERE tenant_id = $1::uuid;
        """
        
        row = await self.postgres_conn.fetchrow(query, tenant_id)
        
        if not row:
            # Initialize balance
            init_query = """
                INSERT INTO ai_token_balances (tenant_id)
                VALUES ($1::uuid)
                RETURNING tokens_purchased, tokens_used, tokens_remaining;
            """
            row = await self.postgres_conn.fetchrow(init_query, tenant_id)
        
        return {
            'tokens_purchased': row['tokens_purchased'] or 0,
            'tokens_used': row['tokens_used'] or 0,
            'tokens_remaining': row['tokens_remaining'] or 0,
            'last_purchase_at': row['last_purchase_at'].isoformat() if row['last_purchase_at'] else None,
            'last_usage_at': row['last_usage_at'].isoformat() if row['last_usage_at'] else None
        }
    
    async def get_usage_history(
        self,
        tenant_id: str,
        limit: int = 100
    ) -> list:
        """DELTA:20251113_064143 Get usage history"""
        query = """
            SELECT usage_id, feature_type, tokens_used, cost_cents, request_id, created_at
            FROM ai_token_usage
            WHERE tenant_id = $1::uuid
            ORDER BY created_at DESC
            LIMIT $2;
        """
        
        rows = await self.postgres_conn.fetch(query, tenant_id, limit)
        
        return [
            {
                'usage_id': str(row['usage_id']),
                'feature_type': row['feature_type'],
                'tokens_used': row['tokens_used'],
                'cost_cents': row['cost_cents'],
                'request_id': row['request_id'],
                'created_at': row['created_at'].isoformat()
            }
            for row in rows
        ]
    
    async def _record_transaction(
        self,
        tenant_id: str,
        transaction_type: str,
        amount_cents: int,
        external_transaction_id: Optional[str] = None,
        description: Optional[str] = None
    ):
        """DELTA:20251113_064143 Record billing transaction"""
        query = """
            INSERT INTO billing_transactions (
                tenant_id, transaction_type, amount_cents, external_transaction_id, description, status
            )
            VALUES ($1::uuid, $2, $3, $4, $5, 'completed');
        """
        
        await self.postgres_conn.execute(
            query,
            tenant_id, transaction_type, amount_cents, external_transaction_id, description
        )
