"""
Content Analyzer

Uses AI to analyze episode content, transcripts, and generate insights.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from uuid import uuid4

from src.ai.framework import AIFramework
from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger
from src.database import PostgresConnection

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """
    Content Analyzer
    
    Analyzes episode content using AI to extract insights, sentiment, topics, etc.
    """
    
    def __init__(
        self,
        ai_framework: AIFramework,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger,
        postgres_conn: PostgresConnection
    ):
        self.ai = ai_framework
        self.metrics = metrics_collector
        self.events = event_logger
        self.postgres = postgres_conn
    
    async def analyze_transcript(
        self,
        tenant_id: str,
        episode_id: str,
        transcript_text: str,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze episode transcript
        
        Returns:
            Dictionary with analysis results:
            - summary: Episode summary
            - sentiment: Sentiment analysis
            - topics: List of topics
            - keywords: List of keywords
            - sponsor_mentions: Sponsor mentions detected
        """
        # Generate summary
        summary_prompt = f"Summarize the following podcast episode transcript in 2-3 sentences:\n\n{transcript_text[:2000]}"
        summary = await self.ai.generate_text(summary_prompt)
        
        # Analyze sentiment
        sentiment = await self.ai.analyze_sentiment(transcript_text[:2000])
        
        # Extract topics
        topics = await self.ai.extract_topics(transcript_text[:2000])
        
        # Extract keywords (simplified - in production, use more sophisticated extraction)
        keywords = topics[:10]  # Use top topics as keywords
        
        # Detect sponsor mentions (simplified - in production, use NER)
        sponsor_mentions = await self._detect_sponsor_mentions(transcript_text)
        
        # Store insight
        insight_id = str(uuid4())
        await self.postgres.execute(
            """
            INSERT INTO ai_insights (
                insight_id, tenant_id, campaign_id, episode_id,
                insight_type, content, summary, sentiment_score,
                topics, keywords, recommendations, confidence_score,
                model_version, metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """,
            insight_id, tenant_id, campaign_id, episode_id,
            "content_analysis", transcript_text[:5000], summary,
            sentiment.get("score", 0.5), topics, keywords, [],
            sentiment.get("confidence", 0.8), "gpt-4", {}
        )
        
        # Record telemetry
        self.metrics.increment_counter(
            "ai_content_analyzed",
            tags={"tenant_id": tenant_id, "episode_id": episode_id}
        )
        
        return {
            "insight_id": insight_id,
            "summary": summary,
            "sentiment": sentiment,
            "topics": topics,
            "keywords": keywords,
            "sponsor_mentions": sponsor_mentions
        }
    
    async def _detect_sponsor_mentions(self, text: str) -> List[Dict[str, Any]]:
        """Detect sponsor mentions in text (simplified)"""
        # In production, use NER or pattern matching
        # For now, return empty list
        return []
    
    async def generate_episode_summary(self, transcript_text: str) -> str:
        """Generate episode summary"""
        prompt = f"Create a concise summary of this podcast episode:\n\n{transcript_text[:3000]}"
        return await self.ai.generate_text(prompt)
    
    async def extract_key_quotes(self, transcript_text: str, count: int = 5) -> List[str]:
        """Extract key quotes from transcript"""
        prompt = f"Extract {count} key quotes from this podcast transcript:\n\n{transcript_text[:3000]}"
        quotes_text = await self.ai.generate_text(prompt)
        # Parse quotes (simplified)
        quotes = [q.strip() for q in quotes_text.split("\n") if q.strip()][:count]
        return quotes
