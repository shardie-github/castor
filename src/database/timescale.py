"""
TimescaleDB Connection

Handles TimescaleDB (PostgreSQL extension) connections for time-series data.
"""

import logging
from typing import Optional
from src.database.postgres import PostgresConnection

logger = logging.getLogger(__name__)


class TimescaleConnection(PostgresConnection):
    """
    TimescaleDB Connection Manager
    
    Extends PostgreSQL connection for TimescaleDB-specific operations.
    """
    
    async def create_hypertable(
        self,
        table_name: str,
        time_column: str = "timestamp",
        partitioning_column: Optional[str] = None
    ):
        """Create a hypertable for time-series data"""
        if partitioning_column:
            query = f"""
                SELECT create_hypertable(
                    '{table_name}',
                    '{time_column}',
                    partitioning_column => '{partitioning_column}',
                    number_partitions => 4
                )
            """
        else:
            query = f"""
                SELECT create_hypertable(
                    '{table_name}',
                    '{time_column}'
                )
            """
        
        try:
            await self.execute(query)
            logger.info(f"Created hypertable: {table_name}")
        except Exception as e:
            logger.error(f"Failed to create hypertable {table_name}: {e}")
            raise
    
    async def create_continuous_aggregate(
        self,
        view_name: str,
        query: str,
        refresh_interval: str = "1 hour"
    ):
        """Create a continuous aggregate view"""
        create_query = f"""
            CREATE MATERIALIZED VIEW {view_name}
            WITH (timescaledb.continuous) AS
            {query}
        """
        
        try:
            await self.execute(create_query)
            
            # Add refresh policy
            refresh_query = f"""
                SELECT add_continuous_aggregate_policy(
                    '{view_name}',
                    start_offset => INTERVAL '1 hour',
                    end_offset => INTERVAL '1 minute',
                    schedule_interval => INTERVAL '{refresh_interval}'
                )
            """
            await self.execute(refresh_query)
            
            logger.info(f"Created continuous aggregate: {view_name}")
        except Exception as e:
            logger.error(f"Failed to create continuous aggregate {view_name}: {e}")
            raise
    
    async def add_retention_policy(
        self,
        table_name: str,
        retention_period: str = "90 days"
    ):
        """Add data retention policy"""
        query = f"""
            SELECT add_retention_policy(
                '{table_name}',
                INTERVAL '{retention_period}'
            )
        """
        
        try:
            await self.execute(query)
            logger.info(f"Added retention policy to {table_name}: {retention_period}")
        except Exception as e:
            logger.error(f"Failed to add retention policy: {e}")
            raise
