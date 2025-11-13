"""
Unit tests for Risk Management
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.operations.risk_management import (
    RiskManager, RiskCategory, RiskStatus, RiskSeverity
)


@pytest.fixture
def mock_postgres():
    """Mock PostgreSQL connection"""
    mock = AsyncMock()
    mock.execute = AsyncMock()
    mock.fetch_one = AsyncMock()
    mock.fetch_all = AsyncMock()
    return mock


@pytest.fixture
def mock_metrics():
    """Mock metrics collector"""
    mock = MagicMock()
    mock.increment_counter = MagicMock()
    return mock


@pytest.fixture
def mock_events():
    """Mock event logger"""
    mock = MagicMock()
    mock.log_event = MagicMock()
    return mock


@pytest.fixture
def risk_manager(mock_postgres, mock_metrics, mock_events):
    """Create RiskManager instance"""
    return RiskManager(
        postgres_conn=mock_postgres,
        metrics_collector=mock_metrics,
        event_logger=mock_events
    )


@pytest.mark.asyncio
async def test_create_risk(risk_manager, mock_postgres):
    """Test creating a risk"""
    mock_postgres.execute = AsyncMock()
    
    risk = await risk_manager.create_risk(
        tenant_id=None,
        category=RiskCategory.SECURITY,
        title="Test Risk",
        description="Test description",
        impact=5,
        probability=4,
        owner="test_owner",
        mitigation_strategies=["Mitigation 1", "Mitigation 2"]
    )
    
    assert risk.risk_id is not None
    assert risk.title == "Test Risk"
    assert risk.impact == 5
    assert risk.probability == 4
    assert risk.risk_score == 20
    assert risk.severity == RiskSeverity.CRITICAL
    assert risk.status == RiskStatus.ACTIVE
    assert mock_postgres.execute.called


@pytest.mark.asyncio
async def test_calculate_risk_score(risk_manager):
    """Test risk score calculation"""
    # Critical risk
    score, severity = risk_manager._calculate_risk_score(5, 5)
    assert score == 25
    assert severity == RiskSeverity.CRITICAL
    
    # High risk
    score, severity = risk_manager._calculate_risk_score(4, 3)
    assert score == 12
    assert severity == RiskSeverity.HIGH
    
    # Medium risk
    score, severity = risk_manager._calculate_risk_score(3, 2)
    assert score == 6
    assert severity == RiskSeverity.MEDIUM
    
    # Low risk
    score, severity = risk_manager._calculate_risk_score(2, 1)
    assert score == 2
    assert severity == RiskSeverity.LOW


@pytest.mark.asyncio
async def test_get_risk(risk_manager, mock_postgres):
    """Test getting a risk"""
    mock_row = {
        "risk_id": "test-id",
        "tenant_id": None,
        "category": "security",
        "title": "Test Risk",
        "description": "Test",
        "impact": 5,
        "probability": 4,
        "risk_score": 20,
        "severity": "critical",
        "status": "active",
        "owner": "test_owner",
        "mitigation_strategies": [],
        "next_review_date": datetime.utcnow() + timedelta(days=90),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "metadata": {}
    }
    mock_postgres.fetch_one = AsyncMock(return_value=mock_row)
    
    risk = await risk_manager.get_risk("test-id")
    
    assert risk is not None
    assert risk.risk_id == "test-id"
    assert risk.title == "Test Risk"


@pytest.mark.asyncio
async def test_list_risks(risk_manager, mock_postgres):
    """Test listing risks"""
    mock_rows = [
        {
            "risk_id": "test-id-1",
            "tenant_id": None,
            "category": "security",
            "title": "Risk 1",
            "description": "Test",
            "impact": 5,
            "probability": 4,
            "risk_score": 20,
            "severity": "critical",
            "status": "active",
            "owner": "owner1",
            "mitigation_strategies": [],
            "next_review_date": datetime.utcnow() + timedelta(days=90),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": {}
        }
    ]
    mock_postgres.fetch_all = AsyncMock(return_value=mock_rows)
    
    risks = await risk_manager.list_risks()
    
    assert len(risks) == 1
    assert risks[0].risk_id == "test-id-1"


@pytest.mark.asyncio
async def test_update_risk(risk_manager, mock_postgres):
    """Test updating a risk"""
    # Mock get_risk
    mock_row = {
        "risk_id": "test-id",
        "tenant_id": None,
        "category": "security",
        "title": "Test Risk",
        "description": "Test",
        "impact": 5,
        "probability": 4,
        "risk_score": 20,
        "severity": "critical",
        "status": "active",
        "owner": "test_owner",
        "mitigation_strategies": [],
        "next_review_date": datetime.utcnow() + timedelta(days=90),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "metadata": {}
    }
    mock_postgres.fetch_one = AsyncMock(return_value=mock_row)
    mock_postgres.execute = AsyncMock()
    
    risk = await risk_manager.update_risk(
        "test-id",
        impact=4,
        probability=3,
        status=RiskStatus.MITIGATED
    )
    
    assert risk is not None
    assert risk.impact == 4
    assert risk.probability == 3
    assert risk.risk_score == 12
    assert risk.severity == RiskSeverity.HIGH
    assert risk.status == RiskStatus.MITIGATED


@pytest.mark.asyncio
async def test_get_risk_summary(risk_manager, mock_postgres):
    """Test getting risk summary"""
    mock_row = {
        "total_risks": 10,
        "critical_risks": 2,
        "high_risks": 3,
        "medium_risks": 3,
        "low_risks": 2,
        "active_risks": 8,
        "mitigated_risks": 2,
        "avg_risk_score": 12.5
    }
    mock_postgres.fetch_one = AsyncMock(return_value=mock_row)
    
    summary = await risk_manager.get_risk_summary()
    
    assert summary["total_risks"] == 10
    assert summary["critical_risks"] == 2
    assert summary["high_risks"] == 3
    assert summary["avg_risk_score"] == 12.5
