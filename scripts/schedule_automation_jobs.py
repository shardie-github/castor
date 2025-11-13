#!/usr/bin/env python3
"""
DELTA:20251113_064143 Automation Jobs Scheduler

Schedules automation jobs using cron or scheduled_tasks table.
Run this script to set up scheduled jobs.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import PostgresConnection
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.agents.automation_jobs import AutomationJobs


async def setup_scheduled_jobs():
    """DELTA:20251113_064143 Set up scheduled jobs"""
    # Initialize connections
    postgres_conn = PostgresConnection(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "podcast_analytics"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "")
    )
    
    metrics_collector = MetricsCollector()
    event_logger = EventLogger(postgres_conn, metrics_collector)
    
    automation_jobs = AutomationJobs(postgres_conn, metrics_collector, event_logger)
    
    # Insert scheduled jobs into scheduled_tasks table
    jobs = [
        {
            'task_name': 'refresh_metrics_daily',
            'task_type': 'function',
            'schedule_cron': '0 2 * * *',  # Daily at 2 AM UTC
            'enabled': True,
            'description': 'Refresh metrics_daily materialized view'
        },
        {
            'task_name': 'check_etl_health',
            'task_type': 'function',
            'schedule_cron': '*/30 * * * *',  # Every 30 minutes
            'enabled': True,
            'description': 'Check ETL import health'
        },
        {
            'task_name': 'check_deal_pipeline_alerts',
            'task_type': 'function',
            'schedule_cron': '0 9 * * *',  # Daily at 9 AM UTC
            'enabled': True,
            'description': 'Check for deal pipeline alerts'
        },
        {
            'task_name': 'recalculate_matches',
            'task_type': 'function',
            'schedule_cron': '0 3 * * 0',  # Weekly on Sunday at 3 AM UTC
            'enabled': True,
            'description': 'Recalculate matchmaking scores'
        }
    ]
    
    for job in jobs:
        query = """
            INSERT INTO scheduled_tasks (
                task_name, task_type, schedule_cron, enabled, description, metadata
            )
            VALUES ($1, $2, $3, $4, $5, '{"automation_job": true}'::jsonb)
            ON CONFLICT (task_name) DO UPDATE
            SET schedule_cron = EXCLUDED.schedule_cron,
                enabled = EXCLUDED.enabled,
                description = EXCLUDED.description;
        """
        
        await postgres_conn.execute(
            query,
            job['task_name'],
            job['task_type'],
            job['schedule_cron'],
            job['enabled'],
            job['description']
        )
        
        print(f"✓ Scheduled job: {job['task_name']} ({job['schedule_cron']})")
    
    print("\nScheduled jobs configured successfully!")
    print("\nNote: Ensure you have a cron runner or task scheduler that reads from scheduled_tasks table.")


if __name__ == "__main__":
    asyncio.run(setup_scheduled_jobs())
