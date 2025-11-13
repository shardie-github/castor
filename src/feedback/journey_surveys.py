"""
Journey-Based Survey System

Triggers surveys at key journey stages and tracks completion metrics by persona.
Integrates with user journeys and feature completion events.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.users.user_manager import User

logger = logging.getLogger(__name__)


class SurveyTrigger(Enum):
    """Survey trigger types"""
    FEATURE_COMPLETED = "feature_completed"
    STEP_COMPLETED = "step_completed"
    JOURNEY_STAGE_COMPLETED = "journey_stage_completed"
    VALUE_DELIVERED = "value_delivered"
    TIME_BASED = "time_based"
    ERROR_ENCOUNTERED = "error_encountered"


class SurveyType(Enum):
    """Survey types"""
    TIME_TO_VALUE = "time_to_value"
    REPORT_ACCURACY = "report_accuracy"
    RENEWAL_SUCCESS = "renewal_success"
    FEATURE_SATISFACTION = "feature_satisfaction"
    SUPPORT_INCIDENT = "support_incident"
    ONBOARDING_EXPERIENCE = "onboarding_experience"
    CAMPAIGN_SETUP = "campaign_setup"
    REPORT_GENERATION = "report_generation"


@dataclass
class SurveyQuestion:
    """Survey question"""
    question_id: str
    question_text: str
    question_type: str  # rating, multiple_choice, text, nps
    options: Optional[List[str]] = None
    required: bool = True


@dataclass
class Survey:
    """Survey definition"""
    survey_id: str
    survey_type: SurveyType
    trigger: SurveyTrigger
    trigger_context: Dict[str, Any]  # Context that triggered the survey
    questions: List[SurveyQuestion]
    persona_segments: List[str]  # Which personas should see this
    journey_stage: Optional[str] = None
    feature: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = True


@dataclass
class SurveyResponse:
    """Survey response"""
    response_id: str
    survey_id: str
    user_id: str
    persona_segment: str
    responses: Dict[str, Any]  # question_id -> answer
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class JourneySurveySystem:
    """
    Journey-Based Survey System
    
    Triggers surveys at key journey stages and tracks metrics by persona.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self._surveys: Dict[str, Survey] = {}
        self._responses: Dict[str, List[SurveyResponse]] = {}
        self._initialize_default_surveys()
        
    def _initialize_default_surveys(self):
        """Initialize default surveys for key journey stages"""
        
        # Time-to-value survey (after first report generation)
        time_to_value_survey = Survey(
            survey_id="time_to_value",
            survey_type=SurveyType.TIME_TO_VALUE,
            trigger=SurveyTrigger.VALUE_DELIVERED,
            trigger_context={"value_type": "report_generated"},
            questions=[
                SurveyQuestion(
                    question_id="time_to_value",
                    question_text="How long did it take you to generate your first report?",
                    question_type="rating",
                    options=["<15 minutes", "15-30 minutes", "30-60 minutes", "1-2 hours", ">2 hours"]
                ),
                SurveyQuestion(
                    question_id="ease_of_setup",
                    question_text="How easy was it to set up and generate your first report?",
                    question_type="rating",
                    options=["Very Easy", "Easy", "Neutral", "Difficult", "Very Difficult"]
                ),
                SurveyQuestion(
                    question_id="value_perceived",
                    question_text="Did generating this report provide value to you?",
                    question_type="multiple_choice",
                    options=["Yes, significant value", "Yes, some value", "Not sure yet", "No, no value"]
                )
            ],
            persona_segments=["solo_podcaster", "producer", "agency"],
            journey_stage="first_value_delivered",
            feature="report_generation"
        )
        self._surveys[time_to_value_survey.survey_id] = time_to_value_survey
        
        # Report accuracy survey (after report sent to sponsor)
        report_accuracy_survey = Survey(
            survey_id="report_accuracy",
            survey_type=SurveyType.REPORT_ACCURACY,
            trigger=SurveyTrigger.FEATURE_COMPLETED,
            trigger_context={"feature": "report_shared"},
            questions=[
                SurveyQuestion(
                    question_id="accuracy_rating",
                    question_text="How accurate was the data in your report?",
                    question_type="rating",
                    options=["Very Accurate", "Accurate", "Somewhat Accurate", "Inaccurate", "Very Inaccurate"]
                ),
                SurveyQuestion(
                    question_id="sponsor_feedback",
                    question_text="Did your sponsor provide feedback on the report?",
                    question_type="multiple_choice",
                    options=["Yes, positive", "Yes, negative", "Yes, neutral", "No feedback yet", "Not applicable"]
                ),
                SurveyQuestion(
                    question_id="data_issues",
                    question_text="Did you notice any data discrepancies or issues?",
                    question_type="text",
                    required=False
                )
            ],
            persona_segments=["solo_podcaster", "producer", "agency"],
            journey_stage="report_delivery",
            feature="report_generation"
        )
        self._surveys[report_accuracy_survey.survey_id] = report_accuracy_survey
        
        # Renewal success survey (after campaign ends)
        renewal_success_survey = Survey(
            survey_id="renewal_success",
            survey_type=SurveyType.RENEWAL_SUCCESS,
            trigger=SurveyTrigger.JOURNEY_STAGE_COMPLETED,
            trigger_context={"journey_stage": "campaign_completed"},
            questions=[
                SurveyQuestion(
                    question_id="renewal_status",
                    question_text="Did your sponsor renew the campaign?",
                    question_type="multiple_choice",
                    options=["Yes, renewed", "Yes, renewed with higher rate", "No, did not renew", "Still negotiating", "Not applicable"]
                ),
                SurveyQuestion(
                    question_id="renewal_tools_used",
                    question_text="Did you use renewal insights or tools to help with renewal?",
                    question_type="multiple_choice",
                    options=["Yes, extensively", "Yes, somewhat", "No, did not use", "Not available"]
                ),
                SurveyQuestion(
                    question_id="renewal_factors",
                    question_text="What factors influenced the renewal decision? (Select all that apply)",
                    question_type="multiple_choice",
                    options=["Report quality", "ROI data", "Attribution accuracy", "Campaign performance", "Relationship", "Other"],
                    required=False
                )
            ],
            persona_segments=["solo_podcaster", "producer", "agency"],
            journey_stage="renewal_discussion",
            feature="renewal_tools"
        )
        self._surveys[renewal_success_survey.survey_id] = renewal_success_survey
        
        # Support incident survey (after support contact)
        support_incident_survey = Survey(
            survey_id="support_incident",
            survey_type=SurveyType.SUPPORT_INCIDENT,
            trigger=SurveyTrigger.ERROR_ENCOUNTERED,
            trigger_context={"error_type": "support_contacted"},
            questions=[
                SurveyQuestion(
                    question_id="issue_resolved",
                    question_text="Was your issue resolved?",
                    question_type="multiple_choice",
                    options=["Yes, completely", "Yes, partially", "No, not resolved", "Still working on it"]
                ),
                SurveyQuestion(
                    question_id="support_rating",
                    question_text="How would you rate the support you received?",
                    question_type="rating",
                    options=["Excellent", "Good", "Fair", "Poor", "Very Poor"]
                ),
                SurveyQuestion(
                    question_id="could_have_been_prevented",
                    question_text="Do you think this issue could have been prevented with better documentation or UI?",
                    question_type="multiple_choice",
                    options=["Yes, definitely", "Yes, possibly", "No, not preventable", "Not sure"]
                )
            ],
            persona_segments=["solo_podcaster", "producer", "agency", "brand", "data_marketer"],
            journey_stage="support_flow",
            feature="support"
        )
        self._surveys[support_incident_survey.survey_id] = support_incident_survey
        
    async def trigger_survey(
        self,
        user: User,
        trigger: SurveyTrigger,
        context: Dict[str, Any],
        feature: Optional[str] = None,
        journey_stage: Optional[str] = None
    ) -> Optional[Survey]:
        """
        Trigger a survey based on event context
        
        Returns:
            Survey if one should be shown, None otherwise
        """
        persona_segment = user.persona_segment or "unknown"
        
        # Find matching surveys
        matching_surveys = []
        for survey in self._surveys.values():
            if not survey.active:
                continue
                
            # Check trigger match
            if survey.trigger != trigger:
                continue
                
            # Check persona match
            if persona_segment not in survey.persona_segments and "all" not in survey.persona_segments:
                continue
                
            # Check context match
            context_match = True
            for key, value in survey.trigger_context.items():
                if context.get(key) != value:
                    context_match = False
                    break
                    
            if not context_match:
                continue
                
            # Check feature/journey match if specified
            if feature and survey.feature and survey.feature != feature:
                continue
            if journey_stage and survey.journey_stage and survey.journey_stage != journey_stage:
                continue
                
            matching_surveys.append(survey)
        
        if not matching_surveys:
            return None
            
        # Return highest priority survey (first match for now)
        survey = matching_surveys[0]
        
        # Check if user already completed this survey recently
        user_responses = self._responses.get(user.user_id, [])
        recent_responses = [
            r for r in user_responses
            if r.survey_id == survey.survey_id
            and (datetime.now(timezone.utc) - r.completed_at).days < 30
        ]
        
        if recent_responses:
            return None  # Already completed recently
        
        # Log survey trigger
        await self.events.log_event(
            event_type="survey_triggered",
            user_id=user.user_id,
            properties={
                "survey_id": survey.survey_id,
                "survey_type": survey.survey_type.value,
                "trigger": trigger.value,
                "persona_segment": persona_segment,
                "feature": feature,
                "journey_stage": journey_stage
            }
        )
        
        return survey
    
    async def submit_response(
        self,
        user: User,
        survey_id: str,
        responses: Dict[str, Any]
    ) -> SurveyResponse:
        """Submit survey response"""
        survey = self._surveys.get(survey_id)
        if not survey:
            raise ValueError(f"Survey {survey_id} not found")
        
        # Validate responses
        for question in survey.questions:
            if question.required and question.question_id not in responses:
                raise ValueError(f"Required question {question.question_id} not answered")
        
        response = SurveyResponse(
            response_id=str(uuid4()),
            survey_id=survey_id,
            user_id=user.user_id,
            persona_segment=user.persona_segment or "unknown",
            responses=responses,
            metadata={
                "survey_type": survey.survey_type.value,
                "journey_stage": survey.journey_stage,
                "feature": survey.feature
            }
        )
        
        # Store response
        if user.user_id not in self._responses:
            self._responses[user.user_id] = []
        self._responses[user.user_id].append(response)
        
        # Record metrics
        self.metrics.increment_counter(
            "survey_response_submitted",
            tags={
                "survey_id": survey_id,
                "survey_type": survey.survey_type.value,
                "persona_segment": response.persona_segment
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="survey_response_submitted",
            user_id=user.user_id,
            properties={
                "response_id": response.response_id,
                "survey_id": survey_id,
                "survey_type": survey.survey_type.value,
                "persona_segment": response.persona_segment
            }
        )
        
        return response
    
    async def get_survey_metrics(
        self,
        survey_type: Optional[SurveyType] = None,
        persona_segment: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get survey metrics aggregated by persona"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        all_responses = []
        for responses in self._responses.values():
            for response in responses:
                if response.completed_at >= cutoff_date:
                    all_responses.append(response)
        
        # Filter by survey type
        if survey_type:
            all_responses = [
                r for r in all_responses
                if self._surveys.get(r.survey_id) and self._surveys[r.survey_id].survey_type == survey_type
            ]
        
        # Filter by persona
        if persona_segment:
            all_responses = [r for r in all_responses if r.persona_segment == persona_segment]
        
        # Aggregate by persona
        metrics_by_persona: Dict[str, Dict[str, Any]] = {}
        
        for response in all_responses:
            persona = response.persona_segment
            if persona not in metrics_by_persona:
                metrics_by_persona[persona] = {
                    "total_responses": 0,
                    "surveys": {},
                    "average_ratings": {}
                }
            
            metrics_by_persona[persona]["total_responses"] += 1
            
            survey = self._surveys.get(response.survey_id)
            if survey:
                survey_type_key = survey.survey_type.value
                if survey_type_key not in metrics_by_persona[persona]["surveys"]:
                    metrics_by_persona[persona]["surveys"][survey_type_key] = 0
                metrics_by_persona[persona]["surveys"][survey_type_key] += 1
        
        return {
            "total_responses": len(all_responses),
            "by_persona": metrics_by_persona,
            "period_days": days
        }
    
    def get_survey(self, survey_id: str) -> Optional[Survey]:
        """Get survey by ID"""
        return self._surveys.get(survey_id)
    
    def list_surveys(
        self,
        survey_type: Optional[SurveyType] = None,
        active_only: bool = True
    ) -> List[Survey]:
        """List surveys"""
        surveys = list(self._surveys.values())
        
        if survey_type:
            surveys = [s for s in surveys if s.survey_type == survey_type]
        
        if active_only:
            surveys = [s for s in surveys if s.active]
        
        return surveys
