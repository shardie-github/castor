"""
DELTA:20251113_064143 Automation Jobs

Background jobs for:
- ETL health monitoring
- Matchmaking recalculation
- Metrics daily refresh
- Deal pipeline alerts
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class AutomationJobs:
    """DELTA:20251113_064143 Automation jobs manager"""
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics = metrics_collector
        self.events = event_logger
        self._running = False
    
    async def check_etl_health(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        DELTA:20251113_064143 Check ETL import health
        
        Monitors:
        - Last successful import time
        - Recent failures
        - Import lag
        """
        try:
            query = """
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'completed') as successful_imports,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed_imports,
                    MAX(started_at) FILTER (WHERE status = 'completed') as last_success,
                    MAX(started_at) as last_import_attempt
                FROM etl_imports
                WHERE started_at >= NOW() - INTERVAL '24 hours'
                  AND ($1::uuid IS NULL OR tenant_id = $1::uuid);
            """
            
            row = await self.postgres_conn.fetchrow(query, tenant_id)
            
            if not row:
                return {
                    'status': 'unknown',
                    'message': 'No imports in last 24 hours'
                }
            
            last_success = row['last_success']
            last_attempt = row['last_import_attempt']
            failed_count = row['failed_imports'] or 0
            success_count = row['successful_imports'] or 0
            
            # Determine health status
            if last_success and (datetime.now(timezone.utc) - last_success) < timedelta(hours=6):
                status = 'healthy'
            elif last_success and (datetime.now(timezone.utc) - last_success) < timedelta(hours=24):
                status = 'degraded'
            else:
                status = 'unhealthy'
            
            # Emit alert if unhealthy
            if status == 'unhealthy':
                await self.events.log_event(
                    event_type='etl.health_alert',
                    user_id=None,
                    properties={
                        'status': status,
                        'last_success': last_success.isoformat() if last_success else None,
                        'failed_count': failed_count
                    }
                )
            
            # Record metrics
            self.metrics.record_gauge(
                'etl_health_status',
                1 if status == 'healthy' else (0.5 if status == 'degraded' else 0),
                tags={'status': status}
            )
            
            return {
                'status': status,
                'last_success': last_success.isoformat() if last_success else None,
                'last_attempt': last_attempt.isoformat() if last_attempt else None,
                'successful_imports_24h': success_count,
                'failed_imports_24h': failed_count
            }
        
        except Exception as e:
            logger.error(f"ETL health check failed: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    async def recalculate_matches(
        self,
        advertiser_id: Optional[str] = None,
        podcast_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        DELTA:20251113_064143 Recalculate matchmaking scores
        
        Can be triggered:
        - On schedule (all matches)
        - On advertiser update (advertiser-specific)
        - On podcast update (podcast-specific)
        """
        try:
            from src.matchmaking.engine import MatchmakingEngine
            
            engine = MatchmakingEngine(
                postgres_conn=self.postgres_conn,
                metrics_collector=self.metrics,
                event_logger=self.events
            )
            
            # Determine scope
            if advertiser_id:
                # Recalculate for one advertiser
                query = """
                    SELECT DISTINCT podcast_id FROM podcasts
                    WHERE tenant_id = $1::uuid;
                """
                podcasts = await self.postgres_conn.fetch(query, tenant_id)
                
                recalculated = 0
                for pod_row in podcasts:
                    result = await engine.calculate_match_score(
                        advertiser_id=advertiser_id,
                        podcast_id=str(pod_row['podcast_id']),
                        tenant_id=tenant_id
                    )
                    recalculated += 1
                
                return {
                    'status': 'completed',
                    'advertiser_id': advertiser_id,
                    'matches_recalculated': recalculated
                }
            
            elif podcast_id:
                # Recalculate for one podcast
                query = """
                    SELECT DISTINCT sponsor_id as advertiser_id FROM campaigns
                    WHERE tenant_id = $1::uuid;
                """
                advertisers = await self.postgres_conn.fetch(query, tenant_id)
                
                recalculated = 0
                for adv_row in advertisers:
                    result = await engine.calculate_match_score(
                        advertiser_id=str(adv_row['advertiser_id']),
                        podcast_id=podcast_id,
                        tenant_id=tenant_id
                    )
                    recalculated += 1
                
                return {
                    'status': 'completed',
                    'podcast_id': podcast_id,
                    'matches_recalculated': recalculated
                }
            
            else:
                # Recalculate all matches (expensive - should be scheduled)
                query = """
                    SELECT DISTINCT c.sponsor_id as advertiser_id, p.podcast_id
                    FROM campaigns c
                    CROSS JOIN podcasts p
                    WHERE c.tenant_id = $1::uuid AND p.tenant_id = $1::uuid;
                """
                pairs = await self.postgres_conn.fetch(query, tenant_id)
                
                recalculated = 0
                for pair in pairs:
                    result = await engine.calculate_match_score(
                        advertiser_id=str(pair['advertiser_id']),
                        podcast_id=str(pair['podcast_id']),
                        tenant_id=tenant_id
                    )
                    recalculated += 1
                
                return {
                    'status': 'completed',
                    'matches_recalculated': recalculated
                }
        
        except Exception as e:
            logger.error(f"Matchmaking recalculation failed: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    async def refresh_metrics_daily(self) -> Dict[str, Any]:
        """DELTA:20251113_064143 Refresh metrics_daily materialized view"""
        try:
            query = "SELECT refresh_metrics_daily();"
            await self.postgres_conn.execute(query)
            
            await self.events.log_event(
                event_type='metrics_daily.refreshed',
                user_id=None,
                properties={}
            )
            
            return {'status': 'completed', 'refreshed_at': datetime.now(timezone.utc).isoformat()}
        
        except Exception as e:
            logger.error(f"Metrics daily refresh failed: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    async def check_deal_pipeline_alerts(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        DELTA:20251113_064143 Check for deal pipeline alerts
        
        Alerts on:
        - Deals stuck in stage > 7 days
        - High-value deals in negotiation > 14 days
        - Lost deals without reason
        """
        try:
            # Stuck deals
            stuck_query = """
                SELECT campaign_id, campaign_name, stage, stage_changed_at, campaign_value
                FROM campaigns
                WHERE tenant_id = $1::uuid
                  AND stage NOT IN ('won', 'lost')
                  AND stage_changed_at < NOW() - INTERVAL '7 days'
                ORDER BY campaign_value DESC NULLS LAST;
            """
            
            stuck_deals = await self.postgres_conn.fetch(stuck_query, tenant_id)
            
            # Long negotiations
            negotiation_query = """
                SELECT campaign_id, campaign_name, stage_changed_at, campaign_value
                FROM campaigns
                WHERE tenant_id = $1::uuid
                  AND stage = 'negotiation'
                  AND stage_changed_at < NOW() - INTERVAL '14 days'
                ORDER BY campaign_value DESC NULLS LAST;
            """
            
            long_negotiations = await self.postgres_conn.fetch(negotiation_query, tenant_id)
            
            # Lost without reason
            lost_query = """
                SELECT campaign_id, campaign_name
                FROM campaigns
                WHERE tenant_id = $1::uuid
                  AND stage = 'lost'
                  AND (notes IS NULL OR notes = '');
            """
            
            lost_no_reason = await self.postgres_conn.fetch(lost_query, tenant_id)
            
            alerts = []
            
            if stuck_deals:
                alerts.append({
                    'type': 'stuck_deals',
                    'count': len(stuck_deals),
                    'deals': [
                        {
                            'campaign_id': str(d['campaign_id']),
                            'campaign_name': d['campaign_name'],
                            'stage': d['stage'],
                            'days_in_stage': (datetime.now(timezone.utc) - d['stage_changed_at']).days
                        }
                        for d in stuck_deals
                    ]
                })
            
            if long_negotiations:
                alerts.append({
                    'type': 'long_negotiations',
                    'count': len(long_negotiations),
                    'deals': [
                        {
                            'campaign_id': str(d['campaign_id']),
                            'campaign_name': d['campaign_name'],
                            'days_in_negotiation': (datetime.now(timezone.utc) - d['stage_changed_at']).days,
                            'value': float(d['campaign_value'] or 0)
                        }
                        for d in long_negotiations
                    ]
                })
            
            if lost_no_reason:
                alerts.append({
                    'type': 'lost_without_reason',
                    'count': len(lost_no_reason),
                    'deals': [
                        {
                            'campaign_id': str(d['campaign_id']),
                            'campaign_name': d['campaign_name']
                        }
                        for d in lost_no_reason
                    ]
                })
            
            # Emit events for alerts
            for alert in alerts:
                await self.events.log_event(
                    event_type='deal_pipeline.alert',
                    user_id=None,
                    properties=alert
                )
            
            return {
                'status': 'completed',
                'alerts': alerts,
                'alert_count': len(alerts)
            }
        
        except Exception as e:
            logger.error(f"Deal pipeline alerts check failed: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    async def run_scheduled_jobs(self, tenant_id: Optional[str] = None):
        """DELTA:20251113_064143 Run all scheduled automation jobs"""
        if self._running:
            logger.warning("Automation jobs already running")
            return
        
        self._running = True
        try:
            logger.info("Running scheduled automation jobs")
            
            # Run jobs
            etl_health = await self.check_etl_health(tenant_id)
            logger.info(f"ETL health check: {etl_health['status']}")
            
            metrics_refresh = await self.refresh_metrics_daily()
            logger.info(f"Metrics daily refresh: {metrics_refresh['status']}")
            
            pipeline_alerts = await self.check_deal_pipeline_alerts(tenant_id)
            logger.info(f"Pipeline alerts: {pipeline_alerts['alert_count']} alerts")
            
            # Note: Matchmaking recalculation is expensive - run separately on schedule
            
            return {
                'etl_health': etl_health,
                'metrics_refresh': metrics_refresh,
                'pipeline_alerts': pipeline_alerts
            }
        
        finally:
            self._running = False
