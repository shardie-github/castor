"""
DELTA:20251113_064143 Dashboard API Routes

Dashboard data endpoints for Creator, Advertiser/Agency, and Ops personas.
"""

import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone

from src.tenants.tenant_isolation import get_current_tenant
from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


class CreatorDashboardResponse(BaseModel):
    """DELTA:20251113_064143 Creator dashboard response"""
    pacing_vs_flight: Dict[str, Any]
    sponsor_revenue: Dict[str, Any]
    makegoods_pending: List[Dict[str, Any]]


class AdvertiserDashboardResponse(BaseModel):
    """DELTA:20251113_064143 Advertiser dashboard response"""
    audience_fit_summary: Dict[str, Any]
    projected_cpm: Dict[str, Any]
    inventory_calendar: List[Dict[str, Any]]


class OpsDashboardResponse(BaseModel):
    """DELTA:20251113_064143 Ops dashboard response"""
    pipeline_forecast: Dict[str, Any]
    win_loss: Dict[str, Any]
    etl_health: Dict[str, Any]


def get_postgres_conn(request: Request) -> PostgresConnection:
    """DELTA:20251113_064143 Get PostgreSQL connection"""
    return request.app.state.postgres_conn


def check_feature_flag() -> bool:
    """DELTA:20251113_064143 Check if dashboard cards are enabled"""
    return os.getenv("ENABLE_NEW_DASHBOARD_CARDS", "false").lower() == "true"


@router.get("/creator", response_model=CreatorDashboardResponse)
async def get_creator_dashboard(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    podcast_id: Optional[str] = Query(None)
):
    """DELTA:20251113_064143 Get creator dashboard data"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Dashboard cards are disabled")
    
    try:
        # 1. Pacing vs Flight
        pacing_query = """
            SELECT 
                io.io_id,
                io.flight_start,
                io.flight_end,
                io.booked_impressions,
                COALESCE(SUM(ae.attribution_data->>'impressions')::numeric, 0) as actual_impressions,
                CASE 
                    WHEN io.flight_end > NOW() THEN 
                        (EXTRACT(EPOCH FROM (NOW() - io.flight_start)) / 
                         EXTRACT(EPOCH FROM (io.flight_end - io.flight_start))) * 100
                    ELSE 100
                END as flight_progress_pct
            FROM io_bookings io
            LEFT JOIN attribution_events ae ON ae.campaign_id = io.campaign_id
            WHERE io.tenant_id = $1::uuid
              AND ($2::uuid IS NULL OR io.campaign_id IN (
                  SELECT campaign_id FROM campaigns WHERE podcast_id = $2::uuid
              ))
              AND io.status IN ('scheduled', 'active')
            GROUP BY io.io_id, io.flight_start, io.flight_end, io.booked_impressions
            ORDER BY io.flight_start DESC
            LIMIT 10;
        """
        
        pacing_rows = await postgres_conn.fetch(pacing_query, tenant_id, podcast_id)
        
        pacing_data = {
            'ios': [
                {
                    'io_id': str(row['io_id']),
                    'flight_start': row['flight_start'].isoformat(),
                    'flight_end': row['flight_end'].isoformat(),
                    'booked_impressions': row['booked_impressions'],
                    'actual_impressions': float(row['actual_impressions']),
                    'flight_progress_pct': float(row['flight_progress_pct']),
                    'pacing_pct': (float(row['actual_impressions']) / row['booked_impressions'] * 100) 
                                  if row['booked_impressions'] else 0
                }
                for row in pacing_rows
            ],
            'summary': {
                'total_booked': sum(row['booked_impressions'] or 0 for row in pacing_rows),
                'total_delivered': sum(float(row['actual_impressions']) for row in pacing_rows),
                'avg_pacing': sum(
                    (float(row['actual_impressions']) / row['booked_impressions'] * 100) 
                    if row['booked_impressions'] else 0 
                    for row in pacing_rows
                ) / len(pacing_rows) if pacing_rows else 0
            }
        }
        
        # 2. Sponsor Revenue (sum of attributed revenue)
        revenue_query = """
            SELECT 
                DATE(ae.timestamp) as day,
                SUM((ae.conversion_data->>'conversion_value')::numeric) as revenue
            FROM attribution_events ae
            JOIN campaigns c ON c.campaign_id = ae.campaign_id
            WHERE ae.tenant_id = $1::uuid
              AND ($2::uuid IS NULL OR c.podcast_id = $2::uuid)
              AND ae.timestamp >= NOW() - INTERVAL '30 days'
              AND ae.conversion_data->>'conversion_value' IS NOT NULL
            GROUP BY DATE(ae.timestamp)
            ORDER BY day DESC;
        """
        
        revenue_rows = await postgres_conn.fetch(revenue_query, tenant_id, podcast_id)
        
        revenue_data = {
            'daily': [
                {
                    'day': row['day'].isoformat(),
                    'revenue': float(row['revenue'] or 0)
                }
                for row in revenue_rows
            ],
            'total_30d': sum(float(row['revenue'] or 0) for row in revenue_rows),
            'trend': 'up' if len(revenue_rows) > 1 and revenue_rows[0]['revenue'] > revenue_rows[-1]['revenue'] else 'down'
        }
        
        # 3. Makegoods Pending
        makegoods_query = """
            SELECT 
                io.io_id,
                io.campaign_id,
                io.flight_end,
                io.booked_impressions,
                COALESCE(SUM(ae.attribution_data->>'impressions')::numeric, 0) as actual_impressions,
                (io.booked_impressions - COALESCE(SUM(ae.attribution_data->>'impressions')::numeric, 0)) as shortfall
            FROM io_bookings io
            LEFT JOIN attribution_events ae ON ae.campaign_id = io.campaign_id
            WHERE io.tenant_id = $1::uuid
              AND ($2::uuid IS NULL OR io.campaign_id IN (
                  SELECT campaign_id FROM campaigns WHERE podcast_id = $2::uuid
              ))
              AND io.status IN ('completed', 'active')
              AND io.flight_end < NOW()
            GROUP BY io.io_id, io.campaign_id, io.flight_end, io.booked_impressions
            HAVING (io.booked_impressions - COALESCE(SUM(ae.attribution_data->>'impressions')::numeric, 0)) > 0
            ORDER BY shortfall DESC;
        """
        
        makegoods_rows = await postgres_conn.fetch(makegoods_query, tenant_id, podcast_id)
        
        makegoods_data = [
            {
                'io_id': str(row['io_id']),
                'campaign_id': str(row['campaign_id']),
                'flight_end': row['flight_end'].isoformat(),
                'booked_impressions': row['booked_impressions'],
                'actual_impressions': float(row['actual_impressions']),
                'shortfall': float(row['shortfall'])
            }
            for row in makegoods_rows
        ]
        
        return CreatorDashboardResponse(
            pacing_vs_flight=pacing_data,
            sponsor_revenue=revenue_data,
            makegoods_pending=makegoods_data
        )
    
    except Exception as e:
        logger.error(f"Creator dashboard failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dashboard failed: {str(e)}")


@router.get("/advertiser", response_model=AdvertiserDashboardResponse)
async def get_advertiser_dashboard(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn),
    advertiser_id: Optional[str] = Query(None)
):
    """DELTA:20251113_064143 Get advertiser dashboard data"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Dashboard cards are disabled")
    
    try:
        # 1. Audience Fit Summary (from matches table)
        fit_query = """
            SELECT 
                m.podcast_id,
                p.title as podcast_title,
                m.score,
                m.rationale,
                m.signals
            FROM matches m
            JOIN podcasts p ON p.podcast_id = m.podcast_id
            WHERE m.tenant_id = $1::uuid
              AND ($2::uuid IS NULL OR m.advertiser_id = $2::uuid)
            ORDER BY m.score DESC
            LIMIT 10;
        """
        
        fit_rows = await postgres_conn.fetch(fit_query, tenant_id, advertiser_id)
        
        fit_data = {
            'matches': [
                {
                    'podcast_id': str(row['podcast_id']),
                    'podcast_title': row['podcast_title'],
                    'score': float(row['score']),
                    'rationale': row['rationale'],
                    'signals': row['signals']
                }
                for row in fit_rows
            ],
            'avg_score': sum(float(row['score']) for row in fit_rows) / len(fit_rows) if fit_rows else 0,
            'top_score': float(fit_rows[0]['score']) if fit_rows else 0
        }
        
        # 2. Projected CPM (from historical data)
        cpm_query = """
            SELECT 
                AVG(io.booked_cpm_cents) as avg_cpm_cents,
                AVG(io.booked_cpm_cents / NULLIF(io.booked_impressions, 0) * 1000) as effective_cpm_cents
            FROM io_bookings io
            JOIN campaigns c ON c.campaign_id = io.campaign_id
            WHERE io.tenant_id = $1::uuid
              AND ($2::uuid IS NULL OR c.sponsor_id = $2::uuid)
              AND io.status = 'completed'
              AND io.booked_cpm_cents IS NOT NULL;
        """
        
        cpm_row = await postgres_conn.fetchrow(cpm_query, tenant_id, advertiser_id)
        
        cpm_data = {
            'avg_cpm_cents': float(cpm_row['avg_cpm_cents'] or 0) if cpm_row else 0,
            'effective_cpm_cents': float(cpm_row['effective_cpm_cents'] or 0) if cpm_row else 0,
            'projected_cpm_cents': float(cpm_row['avg_cpm_cents'] or 0) if cpm_row else 0  # Use historical avg
        }
        
        # 3. Inventory Calendar (episodes with available ad slots)
        calendar_query = """
            SELECT 
                e.episode_id,
                e.title,
                e.publish_date,
                p.title as podcast_title,
                jsonb_array_length(COALESCE(e.ad_slots, '[]'::jsonb)) as ad_slots_count,
                3 - jsonb_array_length(COALESCE(e.ad_slots, '[]'::jsonb)) as available_slots
            FROM episodes e
            JOIN podcasts p ON p.podcast_id = e.podcast_id
            WHERE p.tenant_id = $1::uuid
              AND e.publish_date >= NOW()
              AND e.publish_date <= NOW() + INTERVAL '30 days'
              AND jsonb_array_length(COALESCE(e.ad_slots, '[]'::jsonb)) < 3
            ORDER BY e.publish_date ASC
            LIMIT 50;
        """
        
        calendar_rows = await postgres_conn.fetch(calendar_query, tenant_id)
        
        calendar_data = [
            {
                'episode_id': str(row['episode_id']),
                'episode_title': row['title'],
                'podcast_title': row['podcast_title'],
                'publish_date': row['publish_date'].isoformat(),
                'available_slots': row['available_slots']
            }
            for row in calendar_rows
        ]
        
        return AdvertiserDashboardResponse(
            audience_fit_summary=fit_data,
            projected_cpm=cpm_data,
            inventory_calendar=calendar_data
        )
    
    except Exception as e:
        logger.error(f"Advertiser dashboard failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dashboard failed: {str(e)}")


@router.get("/ops", response_model=OpsDashboardResponse)
async def get_ops_dashboard(
    request: Request = None,
    tenant_id: str = Depends(get_current_tenant),
    postgres_conn: PostgresConnection = Depends(get_postgres_conn)
):
    """DELTA:20251113_064143 Get ops dashboard data"""
    if not check_feature_flag():
        raise HTTPException(status_code=403, detail="Dashboard cards are disabled")
    
    try:
        # 1. Pipeline Forecast (deal stages distribution)
        pipeline_query = """
            SELECT 
                COALESCE(stage, 'lead') as stage,
                COUNT(*) as count,
                SUM(campaign_value) as total_value
            FROM campaigns
            WHERE tenant_id = $1::uuid
              AND status NOT IN ('cancelled', 'completed')
            GROUP BY stage
            ORDER BY 
                CASE stage
                    WHEN 'lead' THEN 1
                    WHEN 'qualified' THEN 2
                    WHEN 'proposal' THEN 3
                    WHEN 'negotiation' THEN 4
                    WHEN 'won' THEN 5
                    WHEN 'lost' THEN 6
                    ELSE 7
                END;
        """
        
        pipeline_rows = await postgres_conn.fetch(pipeline_query, tenant_id)
        
        pipeline_data = {
            'stages': [
                {
                    'stage': row['stage'],
                    'count': row['count'],
                    'total_value': float(row['total_value'] or 0)
                }
                for row in pipeline_rows
            ],
            'total_deals': sum(row['count'] for row in pipeline_rows),
            'total_pipeline_value': sum(float(row['total_value'] or 0) for row in pipeline_rows)
        }
        
        # 2. Win/Loss
        winloss_query = """
            SELECT 
                CASE 
                    WHEN stage = 'won' THEN 'won'
                    WHEN stage = 'lost' THEN 'lost'
                    ELSE 'in_progress'
                END as outcome,
                COUNT(*) as count,
                SUM(campaign_value) as total_value
            FROM campaigns
            WHERE tenant_id = $1::uuid
              AND stage IN ('won', 'lost')
            GROUP BY outcome;
        """
        
        winloss_rows = await postgres_conn.fetch(winloss_query, tenant_id)
        
        won_count = next((r['count'] for r in winloss_rows if r['outcome'] == 'won'), 0)
        lost_count = next((r['count'] for r in winloss_rows if r['outcome'] == 'lost'), 0)
        total_closed = won_count + lost_count
        
        winloss_data = {
            'won': won_count,
            'lost': lost_count,
            'win_rate': (won_count / total_closed * 100) if total_closed > 0 else 0,
            'total_closed': total_closed
        }
        
        # 3. ETL Health (last ingestions)
        etl_query = """
            SELECT 
                import_id,
                source,
                file_name,
                status,
                records_imported,
                records_failed,
                started_at,
                completed_at,
                error_message
            FROM etl_imports
            WHERE tenant_id = $1::uuid
            ORDER BY started_at DESC
            LIMIT 10;
        """
        
        etl_rows = await postgres_conn.fetch(etl_query, tenant_id)
        
        etl_data = {
            'recent_imports': [
                {
                    'import_id': str(row['import_id']),
                    'source': row['source'],
                    'file_name': row['file_name'],
                    'status': row['status'],
                    'records_imported': row['records_imported'],
                    'records_failed': row['records_failed'],
                    'started_at': row['started_at'].isoformat(),
                    'completed_at': row['completed_at'].isoformat() if row['completed_at'] else None,
                    'error_message': row['error_message']
                }
                for row in etl_rows
            ],
            'health_status': 'healthy' if all(r['status'] == 'completed' for r in etl_rows[:5]) else 'degraded',
            'last_import': etl_rows[0]['started_at'].isoformat() if etl_rows else None
        }
        
        return OpsDashboardResponse(
            pipeline_forecast=pipeline_data,
            win_loss=winloss_data,
            etl_health=etl_data
        )
    
    except Exception as e:
        logger.error(f"Ops dashboard failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dashboard failed: {str(e)}")
