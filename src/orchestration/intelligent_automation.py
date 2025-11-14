"""
DELTA:20251113T114706Z Intelligent Automation Engine

AI-powered automation that makes intelligent decisions about when and how to automate processes.
Uses predictive models and business rules to trigger automated actions.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

from src.ai.framework import AIFramework
from src.ai.predictive_engine import PredictiveEngine
from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.orchestration.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)


@dataclass
class AutomationRule:
    """Automation rule definition"""
    rule_id: str
    name: str
    description: str
    trigger_condition: str  # Event or condition
    action: str  # Action to take
    confidence_threshold: float = 0.7  # Minimum confidence to auto-execute
    enabled: bool = True
    requires_approval: bool = False  # If True, create approval task instead of auto-executing


class IntelligentAutomationEngine:
    """
    DELTA:20251113T114706Z Intelligent Automation Engine
    
    Makes intelligent decisions about automation using:
    - Predictive models (win probability, performance forecasts)
    - Business rules and thresholds
    - Historical patterns
    - Risk assessment
    
    Examples:
    - Auto-progress deals based on win probability
    - Auto-create IOs when deals reach 'won' stage
    - Auto-recalculate matches when advertiser/podcast data changes
    - Auto-optimize campaigns based on performance
    """
    
    def __init__(
        self,
        ai_framework: AIFramework,
        predictive_engine: PredictiveEngine,
        workflow_engine: WorkflowEngine,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.ai = ai_framework
        self.predictive = predictive_engine
        self.workflow = workflow_engine
        self.postgres = postgres_conn
        self.metrics = metrics_collector
        self.events = event_logger
        
        # Automation rules
        self._rules: Dict[str, AutomationRule] = {}
        
        # Decision history
        self._decision_history: List[Dict[str, Any]] = []
    
    def register_rule(self, rule: AutomationRule):
        """Register an automation rule"""
        self._rules[rule.rule_id] = rule
        logger.info(f"Registered automation rule: {rule.name}")
    
    async def evaluate_deal_auto_progression(
        self,
        campaign_id: str,
        tenant_id: str,
        current_stage: str
    ) -> Dict[str, Any]:
        """
        Evaluate if deal should auto-progress to next stage
        
        Uses:
        - Win probability prediction
        - Time in current stage
        - Historical conversion rates
        - Deal value
        """
        try:
            # Get deal data
            query = """
                SELECT campaign_id, campaign_name, stage, stage_changed_at, campaign_value,
                       sponsor_id, podcast_id
                FROM campaigns
                WHERE campaign_id = $1::uuid AND tenant_id = $2::uuid;
            """
            deal = await self.postgres.fetchrow(query, campaign_id, tenant_id)
            
            if not deal:
                return {'action': 'skip', 'reason': 'Deal not found'}
            
            # Calculate time in stage
            time_in_stage = (datetime.now(timezone.utc) - deal['stage_changed_at']).days if deal['stage_changed_at'] else 0
            
            # Get historical data for win probability
            historical_query = """
                SELECT stage, COUNT(*) as count,
                       AVG(EXTRACT(EPOCH FROM (stage_changed_at - created_at))/86400) as avg_days_to_stage
                FROM campaigns
                WHERE tenant_id = $1::uuid
                  AND stage IN ('won', 'lost')
                GROUP BY stage;
            """
            historical = await self.postgres.fetch(historical_query, tenant_id)
            
            # Predict win probability
            prediction = await self.predictive.predict_campaign_performance(
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                historical_data={
                    'current_stage': current_stage,
                    'time_in_stage': time_in_stage,
                    'deal_value': float(deal['campaign_value'] or 0)
                }
            )
            
            # Determine next stage
            stage_progression = {
                'lead': 'qualified',
                'qualified': 'proposal',
                'proposal': 'negotiation',
                'negotiation': 'won'
            }
            next_stage = stage_progression.get(current_stage)
            
            if not next_stage:
                return {'action': 'skip', 'reason': 'No next stage'}
            
            # Decision logic
            confidence = 0.5  # Base confidence
            
            # Increase confidence based on time in stage
            if time_in_stage >= 7:
                confidence += 0.2
            
            # Increase confidence for high-value deals
            if deal['campaign_value'] and float(deal['campaign_value']) > 10000:
                confidence += 0.1
            
            # Use AI to evaluate if progression makes sense
            ai_prompt = f"""
            Should a deal in stage '{current_stage}' progress to '{next_stage}'?
            
            Context:
            - Time in current stage: {time_in_stage} days
            - Deal value: ${deal['campaign_value'] or 0}
            - Historical win rate: {self._calculate_win_rate(historical)}
            
            Respond with: YES, NO, or REVIEW
            """
            
            ai_response = await self.ai.generate_text(ai_prompt)
            ai_decision = 'YES' if 'YES' in ai_response.upper() else ('REVIEW' if 'REVIEW' in ai_response.upper() else 'NO')
            
            if ai_decision == 'YES':
                confidence += 0.2
            elif ai_decision == 'NO':
                confidence -= 0.2
            
            # Make decision
            if confidence >= 0.7:
                action = 'auto_progress'
            elif confidence >= 0.5:
                action = 'suggest_progression'  # Create task for review
            else:
                action = 'skip'
            
            decision = {
                'action': action,
                'confidence': confidence,
                'next_stage': next_stage,
                'reasoning': {
                    'time_in_stage': time_in_stage,
                    'deal_value': float(deal['campaign_value'] or 0),
                    'ai_decision': ai_decision,
                    'prediction': prediction
                }
            }
            
            # Log decision
            await self._log_decision('deal_auto_progression', campaign_id, decision)
            
            return decision
        
        except Exception as e:
            logger.error(f"Deal auto-progression evaluation failed: {e}", exc_info=True)
            return {'action': 'skip', 'reason': str(e)}
    
    async def evaluate_io_auto_creation(
        self,
        campaign_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate if IO should be auto-created when deal reaches 'won' stage
        """
        try:
            # Get deal data
            query = """
                SELECT campaign_id, campaign_name, stage, campaign_value,
                       podcast_id, sponsor_id
                FROM campaigns
                WHERE campaign_id = $1::uuid AND tenant_id = $2::uuid;
            """
            deal = await self.postgres.fetchrow(query, campaign_id, tenant_id)
            
            if not deal or deal['stage'] != 'won':
                return {'action': 'skip', 'reason': 'Deal not in won stage'}
            
            # Check if IO already exists
            io_check = """
                SELECT COUNT(*) as count FROM io_bookings
                WHERE campaign_id = $1::uuid AND tenant_id = $2::uuid;
            """
            io_exists = await self.postgres.fetchval(io_check, campaign_id, tenant_id)
            
            if io_exists > 0:
                return {'action': 'skip', 'reason': 'IO already exists'}
            
            # Decision: Auto-create IO for won deals
            confidence = 0.8  # High confidence for won deals
            
            decision = {
                'action': 'auto_create_io',
                'confidence': confidence,
                'reasoning': {
                    'deal_stage': deal['stage'],
                    'deal_value': float(deal['campaign_value'] or 0)
                }
            }
            
            await self._log_decision('io_auto_creation', campaign_id, decision)
            
            return decision
        
        except Exception as e:
            logger.error(f"IO auto-creation evaluation failed: {e}", exc_info=True)
            return {'action': 'skip', 'reason': str(e)}
    
    async def evaluate_match_auto_recalculation(
        self,
        entity_type: str,  # 'advertiser' or 'podcast'
        entity_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate if matches should be auto-recalculated when advertiser/podcast data changes
        """
        try:
            # Check last recalculation time
            query = """
                SELECT MAX(updated_at) as last_recalc
                FROM matches
                WHERE tenant_id = $1::uuid
                  AND ($2 = 'advertiser' AND advertiser_id = $3::uuid
                       OR $2 = 'podcast' AND podcast_id = $3::uuid);
            """
            last_recalc = await self.postgres.fetchval(query, tenant_id, entity_type, entity_id)
            
            # If recalculation happened recently (< 1 hour), skip
            if last_recalc:
                time_since = (datetime.now(timezone.utc) - last_recalc).total_seconds() / 3600
                if time_since < 1:
                    return {'action': 'skip', 'reason': 'Recently recalculated'}
            
            # Decision: Auto-recalculate if data changed
            confidence = 0.9  # High confidence for data change triggers
            
            decision = {
                'action': 'auto_recalculate_matches',
                'confidence': confidence,
                'entity_type': entity_type,
                'entity_id': entity_id
            }
            
            await self._log_decision('match_auto_recalculation', entity_id, decision)
            
            return decision
        
        except Exception as e:
            logger.error(f"Match auto-recalculation evaluation failed: {e}", exc_info=True)
            return {'action': 'skip', 'reason': str(e)}
    
    async def execute_automation_decision(
        self,
        decision: Dict[str, Any],
        context: Dict[str, Any]
    ):
        """Execute an automation decision"""
        action = decision.get('action')
        
        if action == 'auto_progress':
            # Auto-progress deal
            from src.api.deals import router as deals_router
            # Trigger workflow or direct API call
            await self.workflow.handle_event('deal.auto_progress', {
                **context,
                'next_stage': decision.get('next_stage')
            })
        
        elif action == 'auto_create_io':
            # Auto-create IO
            await self.workflow.handle_event('deal.io_auto_create', context)
        
        elif action == 'auto_recalculate_matches':
            # Auto-recalculate matches
            await self.workflow.handle_event('match.auto_recalculate', context)
        
        # Record metrics
        self.metrics.increment_counter(
            'automation_actions_executed',
            tags={'action': action, 'confidence': str(decision.get('confidence', 0))}
        )
    
    def _calculate_win_rate(self, historical: List[Dict[str, Any]]) -> float:
        """Calculate win rate from historical data"""
        if not historical:
            return 0.5  # Default
        
        won_count = next((h['count'] for h in historical if h['stage'] == 'won'), 0)
        lost_count = next((h['count'] for h in historical if h['stage'] == 'lost'), 0)
        
        total = won_count + lost_count
        return won_count / total if total > 0 else 0.5
    
    async def _log_decision(
        self,
        decision_type: str,
        entity_id: str,
        decision: Dict[str, Any]
    ):
        """Log automation decision"""
        self._decision_history.append({
            'decision_type': decision_type,
            'entity_id': entity_id,
            'decision': decision,
            'timestamp': datetime.now(timezone.utc)
        })
        
        # Keep only last 1000 decisions
        if len(self._decision_history) > 1000:
            self._decision_history = self._decision_history[-1000:]
        
        # Log event
        await self.events.log_event(
            event_type='automation.decision_made',
            user_id=None,
            properties={
                'decision_type': decision_type,
                'entity_id': entity_id,
                'action': decision.get('action'),
                'confidence': decision.get('confidence')
            }
        )
