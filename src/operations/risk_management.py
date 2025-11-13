"""
Risk Management System

Tracks, monitors, and mitigates risks across market, technology, compliance, data bias, and security domains.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import uuid

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class RiskCategory(str, Enum):
    """Risk categories"""
    MARKET = "market"
    TECHNOLOGY = "technology"
    COMPLIANCE = "compliance"
    DATA_BIAS = "data_bias"
    SECURITY = "security"
    OPERATIONAL = "operational"


class RiskStatus(str, Enum):
    """Risk status"""
    ACTIVE = "active"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    CLOSED = "closed"
    ARCHIVED = "archived"


class RiskSeverity(str, Enum):
    """Risk severity levels"""
    CRITICAL = "critical"  # Score 20-25
    HIGH = "high"  # Score 12-19
    MEDIUM = "medium"  # Score 6-11
    LOW = "low"  # Score 1-5


@dataclass
class Risk:
    """Risk data model"""
    risk_id: str
    tenant_id: Optional[str]
    category: RiskCategory
    title: str
    description: str
    impact: int  # 1-5 scale
    probability: int  # 1-5 scale
    risk_score: int  # impact * probability
    severity: RiskSeverity
    status: RiskStatus
    owner: str
    mitigation_strategies: List[str]
    next_review_date: datetime
    created_at: datetime
    updated_at: datetime
    metadata: Dict


class RiskManager:
    """Manages risk tracking, scoring, and mitigation"""
    
    def __init__(
        self,
        postgres_conn: PostgresConnection,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.postgres_conn = postgres_conn
        self.metrics_collector = metrics_collector
        self.event_logger = event_logger
    
    def _calculate_risk_score(self, impact: int, probability: int) -> Tuple[int, RiskSeverity]:
        """Calculate risk score and determine severity"""
        score = impact * probability
        
        if score >= 20:
            severity = RiskSeverity.CRITICAL
        elif score >= 12:
            severity = RiskSeverity.HIGH
        elif score >= 6:
            severity = RiskSeverity.MEDIUM
        else:
            severity = RiskSeverity.LOW
        
        return score, severity
    
    async def create_risk(
        self,
        tenant_id: Optional[str],
        category: RiskCategory,
        title: str,
        description: str,
        impact: int,
        probability: int,
        owner: str,
        mitigation_strategies: List[str],
        next_review_date: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> Risk:
        """Create a new risk"""
        risk_id = str(uuid.uuid4())
        risk_score, severity = self._calculate_risk_score(impact, probability)
        
        if next_review_date is None:
            next_review_date = datetime.utcnow() + timedelta(days=90)  # Default to quarterly
        
        risk = Risk(
            risk_id=risk_id,
            tenant_id=tenant_id,
            category=category,
            title=title,
            description=description,
            impact=impact,
            probability=probability,
            risk_score=risk_score,
            severity=severity,
            status=RiskStatus.ACTIVE,
            owner=owner,
            mitigation_strategies=mitigation_strategies,
            next_review_date=next_review_date,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        await self._save_risk(risk)
        
        self.metrics_collector.increment_counter("risks_created_total", {"category": category.value, "severity": severity.value})
        self.event_logger.log_event("risk_created", {
            "risk_id": risk_id,
            "category": category.value,
            "severity": severity.value,
            "risk_score": risk_score
        })
        
        logger.info(f"Created risk {risk_id}: {title} (Score: {risk_score}, Severity: {severity.value})")
        
        return risk
    
    async def _save_risk(self, risk: Risk):
        """Save risk to database"""
        query = """
            INSERT INTO risks (
                risk_id, tenant_id, category, title, description,
                impact, probability, risk_score, severity, status,
                owner, mitigation_strategies, next_review_date,
                created_at, updated_at, metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
            )
            ON CONFLICT (risk_id) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                impact = EXCLUDED.impact,
                probability = EXCLUDED.probability,
                risk_score = EXCLUDED.risk_score,
                severity = EXCLUDED.severity,
                status = EXCLUDED.status,
                owner = EXCLUDED.owner,
                mitigation_strategies = EXCLUDED.mitigation_strategies,
                next_review_date = EXCLUDED.next_review_date,
                updated_at = EXCLUDED.updated_at,
                metadata = EXCLUDED.metadata
        """
        
        await self.postgres_conn.execute(
            query,
            risk.risk_id,
            risk.tenant_id,
            risk.category.value,
            risk.title,
            risk.description,
            risk.impact,
            risk.probability,
            risk.risk_score,
            risk.severity.value,
            risk.status.value,
            risk.owner,
            risk.mitigation_strategies,
            risk.next_review_date,
            risk.created_at,
            risk.updated_at,
            risk.metadata
        )
    
    async def get_risk(self, risk_id: str) -> Optional[Risk]:
        """Get a risk by ID"""
        query = """
            SELECT * FROM risks WHERE risk_id = $1
        """
        
        row = await self.postgres_conn.fetch_one(query, risk_id)
        if not row:
            return None
        
        return self._row_to_risk(row)
    
    async def list_risks(
        self,
        tenant_id: Optional[str] = None,
        category: Optional[RiskCategory] = None,
        status: Optional[RiskStatus] = None,
        severity: Optional[RiskSeverity] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Risk]:
        """List risks with filters"""
        conditions = []
        params = []
        param_idx = 1
        
        if tenant_id:
            conditions.append(f"tenant_id = ${param_idx}")
            params.append(tenant_id)
            param_idx += 1
        
        if category:
            conditions.append(f"category = ${param_idx}")
            params.append(category.value)
            param_idx += 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1
        
        if severity:
            conditions.append(f"severity = ${param_idx}")
            params.append(severity.value)
            param_idx += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM risks
            WHERE {where_clause}
            ORDER BY risk_score DESC, created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        
        params.extend([limit, offset])
        
        rows = await self.postgres_conn.fetch_all(query, *params)
        return [self._row_to_risk(row) for row in rows]
    
    async def update_risk(
        self,
        risk_id: str,
        impact: Optional[int] = None,
        probability: Optional[int] = None,
        status: Optional[RiskStatus] = None,
        owner: Optional[str] = None,
        mitigation_strategies: Optional[List[str]] = None,
        next_review_date: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Risk]:
        """Update a risk"""
        risk = await self.get_risk(risk_id)
        if not risk:
            return None
        
        if impact is not None:
            risk.impact = impact
        if probability is not None:
            risk.probability = probability
        
        # Recalculate score if impact or probability changed
        if impact is not None or probability is not None:
            risk.risk_score, risk.severity = self._calculate_risk_score(risk.impact, risk.probability)
        
        if status is not None:
            risk.status = status
        if owner is not None:
            risk.owner = owner
        if mitigation_strategies is not None:
            risk.mitigation_strategies = mitigation_strategies
        if next_review_date is not None:
            risk.next_review_date = next_review_date
        if metadata is not None:
            risk.metadata = {**risk.metadata, **metadata}
        
        risk.updated_at = datetime.utcnow()
        await self._save_risk(risk)
        
        self.event_logger.log_event("risk_updated", {
            "risk_id": risk_id,
            "severity": risk.severity.value,
            "status": risk.status.value
        })
        
        return risk
    
    async def add_mitigation(
        self,
        risk_id: str,
        mitigation_description: str,
        mitigation_type: str = "action",
        due_date: Optional[datetime] = None,
        owner: Optional[str] = None
    ) -> str:
        """Add a mitigation action to a risk"""
        mitigation_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO risk_mitigations (
                mitigation_id, risk_id, description, mitigation_type,
                status, due_date, owner, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        
        await self.postgres_conn.execute(
            query,
            mitigation_id,
            risk_id,
            mitigation_description,
            mitigation_type,
            "pending",
            due_date,
            owner,
            datetime.utcnow(),
            datetime.utcnow()
        )
        
        self.event_logger.log_event("risk_mitigation_added", {
            "risk_id": risk_id,
            "mitigation_id": mitigation_id
        })
        
        return mitigation_id
    
    async def get_risks_due_for_review(self, days_ahead: int = 7) -> List[Risk]:
        """Get risks that are due for review within the specified days"""
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        query = """
            SELECT * FROM risks
            WHERE status = 'active'
            AND next_review_date <= $1
            ORDER BY next_review_date ASC
        """
        
        rows = await self.postgres_conn.fetch_all(query, cutoff_date)
        return [self._row_to_risk(row) for row in rows]
    
    async def get_risk_summary(self, tenant_id: Optional[str] = None) -> Dict:
        """Get risk summary statistics"""
        conditions = []
        params = []
        
        if tenant_id:
            conditions.append("tenant_id = $1")
            params.append(tenant_id)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT 
                COUNT(*) as total_risks,
                COUNT(*) FILTER (WHERE severity = 'critical') as critical_risks,
                COUNT(*) FILTER (WHERE severity = 'high') as high_risks,
                COUNT(*) FILTER (WHERE severity = 'medium') as medium_risks,
                COUNT(*) FILTER (WHERE severity = 'low') as low_risks,
                COUNT(*) FILTER (WHERE status = 'active') as active_risks,
                COUNT(*) FILTER (WHERE status = 'mitigated') as mitigated_risks,
                AVG(risk_score) as avg_risk_score
            FROM risks
            WHERE {where_clause}
        """
        
        row = await self.postgres_conn.fetch_one(query, *params)
        
        return {
            "total_risks": row["total_risks"] or 0,
            "critical_risks": row["critical_risks"] or 0,
            "high_risks": row["high_risks"] or 0,
            "medium_risks": row["medium_risks"] or 0,
            "low_risks": row["low_risks"] or 0,
            "active_risks": row["active_risks"] or 0,
            "mitigated_risks": row["mitigated_risks"] or 0,
            "avg_risk_score": float(row["avg_risk_score"] or 0)
        }
    
    def _row_to_risk(self, row: Dict) -> Risk:
        """Convert database row to Risk object"""
        return Risk(
            risk_id=row["risk_id"],
            tenant_id=row.get("tenant_id"),
            category=RiskCategory(row["category"]),
            title=row["title"],
            description=row["description"],
            impact=row["impact"],
            probability=row["probability"],
            risk_score=row["risk_score"],
            severity=RiskSeverity(row["severity"]),
            status=RiskStatus(row["status"]),
            owner=row["owner"],
            mitigation_strategies=row.get("mitigation_strategies", []),
            next_review_date=row["next_review_date"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=row.get("metadata", {})
        )
