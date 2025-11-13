"""
Operational Runbooks Module

Handles:
- Rolling deployments with version management
- Versioned onboarding flows
- Automated account health/usage checks
"""

import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.users.user_manager import UserManager, User
from src.campaigns.campaign_manager import CampaignManager
from src.analytics.analytics_store import AnalyticsStore

logger = logging.getLogger(__name__)


class DeploymentStrategy(Enum):
    """Deployment strategies"""
    ROLLING = "rolling"  # Gradual rollout
    CANARY = "canary"  # Small subset first
    BLUE_GREEN = "blue_green"  # Full switchover
    IMMEDIATE = "immediate"  # All at once


class DeploymentStatus(Enum):
    """Deployment status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class HealthStatus(Enum):
    """Account health status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    AT_RISK = "at_risk"


@dataclass
class Deployment:
    """Deployment record"""
    deployment_id: str
    version: str
    strategy: DeploymentStrategy
    status: DeploymentStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    rollback_at: Optional[datetime] = None
    affected_users: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class OnboardingVersion:
    """Onboarding version configuration"""
    version_id: str
    version_name: str
    is_active: bool
    rollout_percentage: float  # 0-100
    target_personas: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    activated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheckResult:
    """Account health check result"""
    user_id: str
    status: HealthStatus
    checks: Dict[str, Any]  # Individual check results
    score: float  # 0-100 health score
    recommendations: List[str] = field(default_factory=list)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    next_check_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=1))


class DeploymentManager:
    """
    Deployment Manager
    
    Handles rolling deployments with version management and gradual rollouts.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        user_manager: UserManager
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.users = user_manager
        self._deployments: Dict[str, Deployment] = {}
        self._current_version: str = "1.0.0"
        
    async def create_deployment(
        self,
        version: str,
        strategy: DeploymentStrategy,
        rollout_percentage: float = 100.0,
        target_personas: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Deployment:
        """
        Create a new deployment
        
        Args:
            version: Version string (e.g., "1.2.0")
            strategy: Deployment strategy
            rollout_percentage: Percentage of users to deploy to (0-100)
            target_personas: Optional list of persona segments to target
            metadata: Additional deployment metadata
            
        Returns:
            Deployment record
        """
        deployment_id = str(uuid4())
        
        deployment = Deployment(
            deployment_id=deployment_id,
            version=version,
            strategy=strategy,
            status=DeploymentStatus.PENDING,
            started_at=datetime.now(timezone.utc),
            metadata=metadata or {}
        )
        
        self._deployments[deployment_id] = deployment
        
        # Log deployment creation
        await self.events.log_event(
            event_type="deployment_created",
            user_id=None,
            properties={
                "deployment_id": deployment_id,
                "version": version,
                "strategy": strategy.value,
                "rollout_percentage": rollout_percentage
            }
        )
        
        self.metrics.increment_counter(
            "deployment_created",
            tags={"version": version, "strategy": strategy.value}
        )
        
        return deployment
    
    async def execute_deployment(
        self,
        deployment_id: str,
        dry_run: bool = False
    ) -> Deployment:
        """
        Execute a deployment
        
        Args:
            deployment_id: Deployment ID
            dry_run: If True, simulate without actual changes
            
        Returns:
            Updated deployment record
        """
        deployment = self._deployments.get(deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")
        
        deployment.status = DeploymentStatus.IN_PROGRESS
        
        try:
            if deployment.strategy == DeploymentStrategy.ROLLING:
                await self._execute_rolling_deployment(deployment, dry_run)
            elif deployment.strategy == DeploymentStrategy.CANARY:
                await self._execute_canary_deployment(deployment, dry_run)
            elif deployment.strategy == DeploymentStrategy.BLUE_GREEN:
                await self._execute_blue_green_deployment(deployment, dry_run)
            else:  # IMMEDIATE
                await self._execute_immediate_deployment(deployment, dry_run)
            
            if not dry_run:
                deployment.status = DeploymentStatus.COMPLETED
                deployment.completed_at = datetime.now(timezone.utc)
                self._current_version = deployment.version
                
                self.metrics.increment_counter(
                    "deployment_completed",
                    tags={"version": deployment.version, "strategy": deployment.strategy.value}
                )
            
        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            
            self.metrics.increment_counter(
                "deployment_failed",
                tags={"version": deployment.version, "error": type(e).__name__}
            )
            
            logger.error(f"Deployment {deployment_id} failed: {e}")
        
        return deployment
    
    async def _execute_rolling_deployment(
        self,
        deployment: Deployment,
        dry_run: bool
    ):
        """Execute rolling deployment (gradual rollout)"""
        # In production, this would:
        # 1. Deploy to small percentage of users
        # 2. Monitor metrics and errors
        # 3. Gradually increase percentage
        # 4. Complete rollout or rollback based on health checks
        
        rollout_percentage = deployment.metadata.get("rollout_percentage", 100.0)
        logger.info(f"Executing rolling deployment {deployment.deployment_id} to {rollout_percentage}% of users")
        
        # Simulate gradual rollout
        steps = [10, 25, 50, 75, 100]
        for step in steps:
            if step > rollout_percentage:
                break
            
            logger.info(f"Rolling out to {step}% of users")
            await asyncio.sleep(0.1)  # Simulate deployment time
            
            # Check health metrics
            if not dry_run:
                health_ok = await self._check_deployment_health(deployment)
                if not health_ok:
                    logger.warning(f"Health check failed at {step}%, rolling back")
                    await self.rollback_deployment(deployment.deployment_id)
                    return
    
    async def _execute_canary_deployment(
        self,
        deployment: Deployment,
        dry_run: bool
    ):
        """Execute canary deployment (small subset first)"""
        # Deploy to small subset (e.g., 5% of users)
        # Monitor for issues
        # If healthy, proceed to full rollout
        
        logger.info(f"Executing canary deployment {deployment.deployment_id}")
        
        # Deploy to canary group (5%)
        await asyncio.sleep(0.1)
        
        if not dry_run:
            health_ok = await self._check_deployment_health(deployment)
            if not health_ok:
                await self.rollback_deployment(deployment.deployment_id)
                return
            
            # Proceed to full rollout
            await self._execute_rolling_deployment(deployment, dry_run)
    
    async def _execute_blue_green_deployment(
        self,
        deployment: Deployment,
        dry_run: bool
    ):
        """Execute blue-green deployment (full switchover)"""
        # Deploy new version to green environment
        # Switch traffic from blue to green
        # Monitor and rollback if needed
        
        logger.info(f"Executing blue-green deployment {deployment.deployment_id}")
        await asyncio.sleep(0.1)
        
        if not dry_run:
            health_ok = await self._check_deployment_health(deployment)
            if not health_ok:
                await self.rollback_deployment(deployment.deployment_id)
    
    async def _execute_immediate_deployment(
        self,
        deployment: Deployment,
        dry_run: bool
    ):
        """Execute immediate deployment (all at once)"""
        logger.info(f"Executing immediate deployment {deployment.deployment_id}")
        await asyncio.sleep(0.1)
    
    async def _check_deployment_health(self, deployment: Deployment) -> bool:
        """Check deployment health metrics"""
        # In production, would check:
        # - Error rates
        # - Latency percentiles
        # - User-reported issues
        # - System metrics
        
        # Placeholder: assume healthy if no errors in metadata
        return deployment.metadata.get("health_check_passed", True)
    
    async def rollback_deployment(self, deployment_id: str) -> Deployment:
        """Rollback a deployment"""
        deployment = self._deployments.get(deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")
        
        deployment.status = DeploymentStatus.ROLLED_BACK
        deployment.rollback_at = datetime.now(timezone.utc)
        
        self.metrics.increment_counter(
            "deployment_rolled_back",
            tags={"version": deployment.version}
        )
        
        await self.events.log_event(
            event_type="deployment_rolled_back",
            user_id=None,
            properties={"deployment_id": deployment_id, "version": deployment.version}
        )
        
        return deployment
    
    def get_current_version(self) -> str:
        """Get current deployed version"""
        return self._current_version
    
    async def get_deployment(self, deployment_id: str) -> Optional[Deployment]:
        """Get deployment by ID"""
        return self._deployments.get(deployment_id)


class OnboardingVersionManager:
    """
    Onboarding Version Manager
    
    Manages versioned onboarding flows with A/B testing and gradual rollouts.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        user_manager: UserManager
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.users = user_manager
        self._versions: Dict[str, OnboardingVersion] = {}
        self._user_assignments: Dict[str, str] = {}  # user_id -> version_id
        
    async def create_onboarding_version(
        self,
        version_name: str,
        rollout_percentage: float = 0.0,
        target_personas: Optional[List[str]] = None,
        features: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OnboardingVersion:
        """
        Create a new onboarding version
        
        Args:
            version_name: Human-readable version name
            rollout_percentage: Percentage of users to assign (0-100)
            target_personas: Optional list of persona segments
            features: List of features in this version
            metadata: Additional metadata
            
        Returns:
            OnboardingVersion
        """
        version_id = str(uuid4())
        
        version = OnboardingVersion(
            version_id=version_id,
            version_name=version_name,
            is_active=False,
            rollout_percentage=rollout_percentage,
            target_personas=target_personas or [],
            features=features or [],
            metadata=metadata or {}
        )
        
        self._versions[version_id] = version
        
        await self.events.log_event(
            event_type="onboarding_version_created",
            user_id=None,
            properties={
                "version_id": version_id,
                "version_name": version_name,
                "rollout_percentage": rollout_percentage
            }
        )
        
        return version
    
    async def activate_version(self, version_id: str) -> OnboardingVersion:
        """Activate an onboarding version"""
        version = self._versions.get(version_id)
        if not version:
            raise ValueError(f"Version {version_id} not found")
        
        version.is_active = True
        version.activated_at = datetime.now(timezone.utc)
        
        self.metrics.increment_counter(
            "onboarding_version_activated",
            tags={"version_id": version_id}
        )
        
        return version
    
    async def assign_user_to_version(
        self,
        user_id: str,
        persona_segment: Optional[str] = None
    ) -> OnboardingVersion:
        """
        Assign a user to an onboarding version
        
        Returns the version assigned to the user
        """
        # Check if user already assigned
        if user_id in self._user_assignments:
            version_id = self._user_assignments[user_id]
            return self._versions[version_id]
        
        # Find active version matching persona
        active_versions = [
            v for v in self._versions.values()
            if v.is_active and (
                not v.target_personas or
                not persona_segment or
                persona_segment in v.target_personas
            )
        ]
        
        if not active_versions:
            # Default version (would be created separately)
            default_version = OnboardingVersion(
                version_id="default",
                version_name="Default Onboarding",
                is_active=True,
                rollout_percentage=100.0,
                target_personas=[],
                features=[]
            )
            self._versions["default"] = default_version
            return default_version
        
        # Assign based on rollout percentage
        # Simple hash-based assignment for consistency
        import hashlib
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        assignment_value = (hash_value % 100) / 100.0
        
        for version in sorted(active_versions, key=lambda v: v.rollout_percentage):
            if assignment_value <= version.rollout_percentage / 100.0:
                self._user_assignments[user_id] = version.version_id
                
                await self.events.log_event(
                    event_type="onboarding_version_assigned",
                    user_id=user_id,
                    properties={
                        "version_id": version.version_id,
                        "version_name": version.version_name,
                        "persona_segment": persona_segment
                    }
                )
                
                return version
        
        # Fallback to first active version
        version = active_versions[0]
        self._user_assignments[user_id] = version.version_id
        return version
    
    async def get_user_version(self, user_id: str) -> Optional[OnboardingVersion]:
        """Get onboarding version assigned to user"""
        version_id = self._user_assignments.get(user_id)
        if version_id:
            return self._versions.get(version_id)
        return None


class AccountHealthMonitor:
    """
    Account Health Monitor
    
    Performs automated account health and usage checks.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        user_manager: UserManager,
        campaign_manager: CampaignManager,
        analytics_store: AnalyticsStore
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.users = user_manager
        self.campaigns = campaign_manager
        self.analytics = analytics_store
        self._health_checks: Dict[str, HealthCheckResult] = {}
        
    async def check_account_health(
        self,
        user_id: str,
        days: int = 30
    ) -> HealthCheckResult:
        """
        Perform comprehensive account health check
        
        Args:
            user_id: User ID to check
            days: Number of days to analyze
            
        Returns:
            HealthCheckResult with status and recommendations
        """
        user = await self.users.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        checks = {}
        recommendations = []
        score = 100.0
        
        # Check 1: Account activity
        activity_score = await self._check_account_activity(user_id, days)
        checks["activity"] = activity_score
        if activity_score["status"] == "low":
            score -= 20
            recommendations.append("Increase account activity to maintain engagement")
        
        # Check 2: Campaign performance
        campaign_score = await self._check_campaign_performance(user_id, days)
        checks["campaigns"] = campaign_score
        if campaign_score["status"] == "poor":
            score -= 15
            recommendations.append("Review campaign performance and optimize")
        
        # Check 3: Feature usage
        usage_score = await self._check_feature_usage(user_id, days)
        checks["usage"] = usage_score
        if usage_score["status"] == "low":
            score -= 10
            recommendations.append("Explore additional features to maximize value")
        
        # Check 4: Support interactions
        support_score = await self._check_support_interactions(user_id, days)
        checks["support"] = support_score
        if support_score["status"] == "high":
            score -= 15
            recommendations.append("Review support interactions - may indicate issues")
        
        # Check 5: Subscription health
        subscription_score = await self._check_subscription_health(user_id)
        checks["subscription"] = subscription_score
        if subscription_score["status"] == "at_risk":
            score -= 25
            recommendations.append("Subscription may be at risk - proactive outreach recommended")
        
        # Determine overall status
        if score >= 80:
            status = HealthStatus.HEALTHY
        elif score >= 60:
            status = HealthStatus.WARNING
        elif score >= 40:
            status = HealthStatus.AT_RISK
        else:
            status = HealthStatus.CRITICAL
        
        result = HealthCheckResult(
            user_id=user_id,
            status=status,
            checks=checks,
            score=score,
            recommendations=recommendations,
            next_check_at=datetime.now(timezone.utc) + timedelta(days=1)
        )
        
        self._health_checks[user_id] = result
        
        # Record metrics
        self.metrics.record_gauge(
            "account_health_score",
            score,
            tags={"user_id": user_id, "status": status.value}
        )
        
        await self.events.log_event(
            event_type="account_health_check",
            user_id=user_id,
            properties={
                "status": status.value,
                "score": score,
                "checks": checks
            }
        )
        
        return result
    
    async def _check_account_activity(
        self,
        user_id: str,
        days: int
    ) -> Dict[str, Any]:
        """Check account activity level"""
        # In production, would query event logs
        # Placeholder logic
        return {
            "status": "normal",  # low, normal, high
            "login_count": 15,
            "days_active": 12,
            "last_activity": datetime.now(timezone.utc) - timedelta(days=2)
        }
    
    async def _check_campaign_performance(
        self,
        user_id: str,
        days: int
    ) -> Dict[str, Any]:
        """Check campaign performance"""
        # In production, would query campaign metrics
        return {
            "status": "good",  # poor, good, excellent
            "active_campaigns": 3,
            "avg_performance": 0.75,
            "renewal_rate": 0.80
        }
    
    async def _check_feature_usage(
        self,
        user_id: str,
        days: int
    ) -> Dict[str, Any]:
        """Check feature usage"""
        # In production, would query feature usage events
        return {
            "status": "normal",  # low, normal, high
            "features_used": 5,
            "total_features": 10,
            "usage_rate": 0.50
        }
    
    async def _check_support_interactions(
        self,
        user_id: str,
        days: int
    ) -> Dict[str, Any]:
        """Check support interaction frequency"""
        # In production, would query support tickets
        return {
            "status": "normal",  # low, normal, high
            "ticket_count": 2,
            "avg_resolution_time_hours": 4.5
        }
    
    async def _check_subscription_health(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Check subscription health and churn risk"""
        user = await self.users.get_user(user_id)
        if not user:
            return {"status": "unknown"}
        
        # In production, would analyze:
        # - Payment history
        # - Usage trends
        # - Engagement signals
        # - Churn prediction models
        
        return {
            "status": "healthy",  # healthy, at_risk, churning
            "subscription_tier": user.subscription_tier.value,
            "days_remaining": 15,
            "churn_probability": 0.15
        }
    
    async def get_health_check(self, user_id: str) -> Optional[HealthCheckResult]:
        """Get latest health check result for user"""
        return self._health_checks.get(user_id)
    
    async def check_all_accounts(
        self,
        batch_size: int = 100,
        days: int = 30
    ) -> List[HealthCheckResult]:
        """
        Check health for all accounts (batch processing)
        
        Args:
            batch_size: Number of accounts to process per batch
            days: Number of days to analyze
            
        Returns:
            List of health check results
        """
        # In production, would query all active users from database
        # For now, return empty list
        results = []
        
        # Process in batches to avoid overwhelming system
        # user_ids = await self._get_active_user_ids()
        # for i in range(0, len(user_ids), batch_size):
        #     batch = user_ids[i:i+batch_size]
        #     batch_results = await asyncio.gather(*[
        #         self.check_account_health(user_id, days)
        #         for user_id in batch
        #     ])
        #     results.extend(batch_results)
        
        return results
