"""
DELTA:20251113_064143 Matchmaking Engine

Computes advertiser-podcast match scores using geo/demo/topic overlaps,
historical lift, inventory fit, and brand safety signals.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from uuid import uuid4

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class MatchmakingEngine:
    """
    DELTA:20251113_064143 Matchmaking Engine
    
    Computes match scores (0-100) for advertiser-podcast pairs.
    """
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics_collector = metrics_collector
        self.event_logger = event_logger
    
    async def calculate_match_score(
        self,
        advertiser_id: str,
        podcast_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Calculate match score for advertiser-podcast pair
        
        Returns:
            Dict with 'score' (0-100), 'rationale' (text), 'signals' (JSONB)
        """
        signals = {}
        rationale_parts = []
        
        # 1. Geo Overlap (if available)
        geo_score = await self._calculate_geo_overlap(advertiser_id, podcast_id, tenant_id)
        signals['geo_overlap'] = geo_score
        if geo_score > 0:
            rationale_parts.append(f"Geo overlap: {geo_score:.1%}")
        
        # 2. Demographic Overlap (if available)
        demo_score = await self._calculate_demo_overlap(advertiser_id, podcast_id, tenant_id)
        signals['demographic_overlap'] = demo_score
        if demo_score > 0:
            rationale_parts.append(f"Demographic overlap: {demo_score:.1%}")
        
        # 3. Topic Overlap (if available)
        topic_score = await self._calculate_topic_overlap(advertiser_id, podcast_id, tenant_id)
        signals['topic_overlap'] = topic_score
        if topic_score > 0:
            rationale_parts.append(f"Topic overlap: {topic_score:.1%}")
        
        # 4. Historical Lift (if available)
        lift_score = await self._calculate_historical_lift(advertiser_id, podcast_id, tenant_id)
        signals['historical_lift'] = lift_score
        if lift_score > 0:
            rationale_parts.append(f"Historical lift: {lift_score:.1%}")
        
        # 5. Inventory Fit
        inventory_score = await self._calculate_inventory_fit(podcast_id, tenant_id)
        signals['inventory_fit'] = inventory_score
        if inventory_score > 0:
            rationale_parts.append(f"Inventory fit: {inventory_score:.1%}")
        
        # 6. Brand Safety
        brand_safety_score = await self._calculate_brand_safety(podcast_id, tenant_id)
        signals['brand_safety'] = brand_safety_score
        if brand_safety_score < 1.0:
            rationale_parts.append(f"Brand safety: {brand_safety_score:.1%}")
        
        # Weighted sum (normalize to 0-100)
        # Weights: geo=0.15, demo=0.20, topic=0.25, lift=0.20, inventory=0.15, brand_safety=0.05 (penalty)
        weighted_score = (
            geo_score * 0.15 +
            demo_score * 0.20 +
            topic_score * 0.25 +
            lift_score * 0.20 +
            inventory_score * 0.15 +
            brand_safety_score * 0.05
        ) * 100
        
        # Apply brand safety penalty (if < 1.0, reduce score)
        if brand_safety_score < 1.0:
            weighted_score *= brand_safety_score
        
        final_score = max(0, min(100, weighted_score))
        
        rationale = "; ".join(rationale_parts) if rationale_parts else "Insufficient data for scoring"
        
        return {
            'score': round(final_score, 2),
            'rationale': rationale,
            'signals': signals
        }
    
    async def _calculate_geo_overlap(
        self,
        advertiser_id: str,
        podcast_id: str,
        tenant_id: str
    ) -> float:
        """Calculate geographic overlap (0-1)"""
        # Placeholder: If advertiser/sponsor has target_geo metadata, compare with podcast listener geo
        # For now, return 0.5 (neutral)
        return 0.5
    
    async def _calculate_demo_overlap(
        self,
        advertiser_id: str,
        podcast_id: str,
        tenant_id: str
    ) -> float:
        """Calculate demographic overlap (0-1)"""
        # Placeholder: Compare advertiser target demographics with podcast listener demographics
        # For now, return 0.5 (neutral)
        return 0.5
    
    async def _calculate_topic_overlap(
        self,
        advertiser_id: str,
        podcast_id: str,
        tenant_id: str
    ) -> float:
        """Calculate topic overlap (0-1)"""
        # Placeholder: Compare advertiser industry/category with podcast categories
        # For now, return 0.5 (neutral)
        return 0.5
    
    async def _calculate_historical_lift(
        self,
        advertiser_id: str,
        podcast_id: str,
        tenant_id: str
    ) -> float:
        """Calculate historical lift (0-1)"""
        # Check if advertiser has previous campaigns with this podcast
        query = """
            SELECT COUNT(*) as campaign_count,
                   AVG(attributed_conversions) as avg_conversions
            FROM campaigns c
            JOIN attribution_events ae ON ae.campaign_id = c.campaign_id
            WHERE c.sponsor_id = $1::uuid
              AND c.podcast_id = $2::uuid
              AND c.tenant_id = $3::uuid
              AND c.status = 'completed';
        """
        
        row = await self.postgres_conn.fetchrow(query, advertiser_id, podcast_id, tenant_id)
        
        if row and row['campaign_count'] > 0:
            # Normalize: if avg_conversions > 0, return higher score
            # For now, return 0.7 if historical data exists
            return 0.7
        
        return 0.3  # No historical data
    
    async def _calculate_inventory_fit(
        self,
        podcast_id: str,
        tenant_id: str
    ) -> float:
        """Calculate inventory fit (0-1) - availability of ad slots"""
        # Check for available episodes with ad slots
        query = """
            SELECT COUNT(*) as episode_count
            FROM episodes e
            WHERE e.podcast_id = $1::uuid
              AND e.publish_date > NOW() - INTERVAL '30 days'
              AND (e.ad_slots IS NULL OR jsonb_array_length(e.ad_slots) < 3);
        """
        
        row = await self.postgres_conn.fetchrow(query, podcast_id)
        
        if row and row['episode_count'] > 0:
            # Normalize: more episodes = better fit
            return min(1.0, row['episode_count'] / 10.0)
        
        return 0.2  # Low inventory
    
    async def _calculate_brand_safety(
        self,
        podcast_id: str,
        tenant_id: str
    ) -> float:
        """Calculate brand safety score (0-1) - explicit content check"""
        # Check if podcast/episodes are marked explicit
        query = """
            SELECT COUNT(*) FILTER (WHERE explicit = TRUE) as explicit_count,
                   COUNT(*) as total_episodes
            FROM episodes
            WHERE podcast_id = $1::uuid;
        """
        
        row = await self.postgres_conn.fetchrow(query, podcast_id)
        
        if row and row['total_episodes'] > 0:
            explicit_ratio = row['explicit_count'] / row['total_episodes']
            # Penalize explicit content
            return max(0.0, 1.0 - explicit_ratio * 0.5)
        
        return 1.0  # No explicit content detected
    
    async def save_match(
        self,
        advertiser_id: str,
        podcast_id: str,
        tenant_id: str,
        score: float,
        rationale: str,
        signals: Dict[str, Any]
    ) -> str:
        """Save match to matches table"""
        import json
        
        match_id = str(uuid4())
        
        query = """
            INSERT INTO matches (
                match_id, tenant_id, advertiser_id, podcast_id,
                score, rationale, signals, created_at, updated_at
            )
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4::uuid, $5, $6, $7::jsonb, NOW(), NOW())
            ON CONFLICT (tenant_id, advertiser_id, podcast_id)
            DO UPDATE SET
                score = EXCLUDED.score,
                rationale = EXCLUDED.rationale,
                signals = EXCLUDED.signals,
                updated_at = NOW()
            RETURNING match_id;
        """
        
        result = await self.postgres_conn.fetchval(
            query,
            match_id,
            tenant_id,
            advertiser_id,
            podcast_id,
            score,
            rationale,
            json.dumps(signals)
        )
        
        return str(result)
