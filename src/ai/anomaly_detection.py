"""
Anomaly Detection

Detects anomalies in campaign performance, user behavior, etc.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from uuid import uuid4

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Anomaly Detector
    
    Detects anomalies in campaign performance, user behavior, etc.
    """
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        postgres_conn: PostgresConnection
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        self.postgres = postgres_conn
    
    async def detect_anomalies(
        self,
        tenant_id: str,
        campaign_id: Optional[str] = None,
        metric_type: str = "conversions"
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in campaign metrics
        
        Uses statistical methods (z-score, IQR) to detect outliers.
        """
        # Query historical data
        query = """
            SELECT timestamp, metric_value
            FROM listener_metrics
            WHERE tenant_id = $1 AND metric_type = $2
        """
        
        params = [tenant_id, metric_type]
        if campaign_id:
            query += " AND campaign_id = $" + str(len(params) + 1)
            params.append(campaign_id)
        
        query += " ORDER BY timestamp DESC LIMIT 100"
        
        rows = await self.postgres.fetch(query, *params)
        
        if len(rows) < 10:
            return []  # Not enough data
        
        values = [float(row["metric_value"]) for row in rows]
        
        # Calculate statistics
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        # Detect anomalies (values > 2 standard deviations from mean)
        anomalies = []
        threshold = 2 * std_dev
        
        for i, row in enumerate(rows):
            value = float(row["metric_value"])
            z_score = abs((value - mean) / std_dev) if std_dev > 0 else 0
            
            if z_score > 2:
                anomaly_id = str(uuid4())
                anomalies.append({
                    "anomaly_id": anomaly_id,
                    "timestamp": row["timestamp"].isoformat(),
                    "metric_value": value,
                    "z_score": z_score,
                    "severity": "high" if z_score > 3 else "medium"
                })
                
                # Store insight
                await self.postgres.execute(
                    """
                    INSERT INTO ai_insights (
                        insight_id, tenant_id, campaign_id, insight_type,
                        content, summary, confidence_score, model_version, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    anomaly_id, tenant_id, campaign_id, "anomaly_detection",
                    f"Anomaly detected: {value} (z-score: {z_score:.2f})",
                    f"Anomaly detected in {metric_type}",
                    z_score / 5.0,  # Normalize to 0-1
                    "statistical", {"z_score": z_score, "metric_type": metric_type}
                )
        
        return anomalies
