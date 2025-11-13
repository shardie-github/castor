"""
DELTA:20251113_064143 Matchmaking API Routes

Advertiser-podcast matchmaking endpoint.
"""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi import Request
from pydantic import BaseModel
from typing import Optional

from src.matchmaking.engine import MatchmakingEngine
from src.tenants.tenant_isolation import get_current_tenant
from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/match", tags=["matchmaking"])


class MatchResponse(BaseModel):
    """DELTA:20251113_064143 Match response"""
    match_id: str
    advertiser_id: str
    podcast_id: str
    score: float
    rationale: str
    signals: dict


def get_matchmaking_engine(request: Request) -> MatchmakingEngine:
    """DELTA:20251113_064143 Get matchmaking engine"""
    postgres_conn: PostgresConnection = request.app.state.postgres_conn
    metrics_collector: MetricsCollector = request.app.state.metrics_collector
    event_logger: EventLogger = request.app.state.event_logger
    
    return MatchmakingEngine(
        postgres_conn=postgres_conn,
        metrics_collector=metrics_collector,
        event_logger=event_logger
    )


def check_feature_flag() -> bool:
    """DELTA:20251113_064143 Check if matchmaking is enabled"""
    return os.getenv("ENABLE_MATCHMAKING", "false").lower() == "true"


@router.post("/recalculate", response_model=MatchResponse, status_code=status.HTTP_200_OK)
async def recalculate_match(
    advertiser_id: Optional[str] = Query(None, description="Advertiser ID (sponsor_id)"),
    podcast_id: Optional[str] = Query(None, description="Podcast ID"),
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    engine: MatchmakingEngine = Depends(get_matchmaking_engine)
):
    """
    DELTA:20251113_064143 Recalculate match scores
    
    - If both advertiser_id and podcast_id provided: recalc single match
    - If one provided: recalc all matches for that entity
    - If neither: recalc all matches (admin only - requires additional auth check)
    """
    # Check feature flag
    if not check_feature_flag():
        raise HTTPException(
            status_code=403,
            detail="Matchmaking is disabled. Set ENABLE_MATCHMAKING=true to enable."
        )
    
    # Validate inputs
    if not advertiser_id and not podcast_id:
        # Admin-only: recalc all matches
        # In production, add admin role check here
        raise HTTPException(
            status_code=400,
            detail="Either advertiser_id or podcast_id must be provided"
        )
    
    try:
        # Calculate match score
        if advertiser_id and podcast_id:
            # Single match
            result = await engine.calculate_match_score(
                advertiser_id=advertiser_id,
                podcast_id=podcast_id,
                tenant_id=tenant_id
            )
            
            # Save match
            match_id = await engine.save_match(
                advertiser_id=advertiser_id,
                podcast_id=podcast_id,
                tenant_id=tenant_id,
                score=result['score'],
                rationale=result['rationale'],
                signals=result['signals']
            )
            
            # Emit event
            await request.app.state.event_logger.log_event(
                event_type='match.recalculated',
                user_id=None,
                properties={
                    'match_id': match_id,
                    'advertiser_id': advertiser_id,
                    'podcast_id': podcast_id,
                    'score': result['score']
                }
            )
            
            return MatchResponse(
                match_id=match_id,
                advertiser_id=advertiser_id,
                podcast_id=podcast_id,
                score=result['score'],
                rationale=result['rationale'],
                signals=result['signals']
            )
        
        elif advertiser_id:
            # Recalc all matches for advertiser
            # Get all podcasts for tenant
            query = """
                SELECT podcast_id FROM podcasts
                WHERE tenant_id = $1::uuid;
            """
            podcasts = await engine.postgres_conn.fetch(query, tenant_id)
            
            matches = []
            for podcast_row in podcasts:
                pod_id = str(podcast_row['podcast_id'])
                result = await engine.calculate_match_score(
                    advertiser_id=advertiser_id,
                    podcast_id=pod_id,
                    tenant_id=tenant_id
                )
                
                match_id = await engine.save_match(
                    advertiser_id=advertiser_id,
                    podcast_id=pod_id,
                    tenant_id=tenant_id,
                    score=result['score'],
                    rationale=result['rationale'],
                    signals=result['signals']
                )
                
                matches.append({
                    'match_id': match_id,
                    'podcast_id': pod_id,
                    'score': result['score']
                })
            
            # Emit event
            await request.app.state.event_logger.log_event(
                event_type='match.recalculated',
                user_id=None,
                properties={
                    'advertiser_id': advertiser_id,
                    'matches_count': len(matches)
                }
            )
            
            # Return first match (or could return list)
            if matches:
                first_match = matches[0]
                # Get full details
                full_result = await engine.calculate_match_score(
                    advertiser_id=advertiser_id,
                    podcast_id=first_match['podcast_id'],
                    tenant_id=tenant_id
                )
                return MatchResponse(
                    match_id=first_match['match_id'],
                    advertiser_id=advertiser_id,
                    podcast_id=first_match['podcast_id'],
                    score=full_result['score'],
                    rationale=full_result['rationale'],
                    signals=full_result['signals']
                )
            else:
                raise HTTPException(status_code=404, detail="No podcasts found")
        
        elif podcast_id:
            # Recalc all matches for podcast
            # Get all advertisers (sponsors) for tenant
            query = """
                SELECT sponsor_id FROM sponsors
                WHERE tenant_id = $1::uuid;
            """
            advertisers = await engine.postgres_conn.fetch(query, tenant_id)
            
            matches = []
            for advertiser_row in advertisers:
                adv_id = str(advertiser_row['sponsor_id'])
                result = await engine.calculate_match_score(
                    advertiser_id=adv_id,
                    podcast_id=podcast_id,
                    tenant_id=tenant_id
                )
                
                match_id = await engine.save_match(
                    advertiser_id=adv_id,
                    podcast_id=podcast_id,
                    tenant_id=tenant_id,
                    score=result['score'],
                    rationale=result['rationale'],
                    signals=result['signals']
                )
                
                matches.append({
                    'match_id': match_id,
                    'advertiser_id': adv_id,
                    'score': result['score']
                })
            
            # Emit event
            await request.app.state.event_logger.log_event(
                event_type='match.recalculated',
                user_id=None,
                properties={
                    'podcast_id': podcast_id,
                    'matches_count': len(matches)
                }
            )
            
            # Return first match
            if matches:
                first_match = matches[0]
                full_result = await engine.calculate_match_score(
                    advertiser_id=first_match['advertiser_id'],
                    podcast_id=podcast_id,
                    tenant_id=tenant_id
                )
                return MatchResponse(
                    match_id=first_match['match_id'],
                    advertiser_id=first_match['advertiser_id'],
                    podcast_id=podcast_id,
                    score=full_result['score'],
                    rationale=full_result['rationale'],
                    signals=full_result['signals']
                )
            else:
                raise HTTPException(status_code=404, detail="No advertisers found")
    
    except Exception as e:
        logger.error(f"Matchmaking recalculation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Matchmaking failed: {str(e)}"
        )
