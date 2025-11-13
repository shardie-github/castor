"""
AI Features API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from src.ai import ContentAnalyzer
from src.tenants.tenant_isolation import get_current_tenant
from fastapi import Request

router = APIRouter()


class TranscriptAnalysisRequest(BaseModel):
    episode_id: str
    transcript_text: str
    campaign_id: Optional[str] = None


class TranscriptAnalysisResponse(BaseModel):
    insight_id: str
    summary: str
    sentiment: Dict[str, Any]
    topics: List[str]
    keywords: List[str]
    sponsor_mentions: List[Dict[str, Any]]


def get_content_analyzer(request: Request) -> ContentAnalyzer:
    return request.app.state.content_analyzer


@router.post("/analyze-transcript", response_model=TranscriptAnalysisResponse)
async def analyze_transcript(
    request_data: TranscriptAnalysisRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant),
    content_analyzer: ContentAnalyzer = Depends(get_content_analyzer)
):
    """Analyze episode transcript using AI"""
    result = await content_analyzer.analyze_transcript(
        tenant_id=tenant_id,
        episode_id=request_data.episode_id,
        transcript_text=request_data.transcript_text,
        campaign_id=request_data.campaign_id
    )
    
    return TranscriptAnalysisResponse(**result)
