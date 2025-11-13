"""
Ad Slot Detection Module

Detects advertisement slots in podcast episodes using:
- Audio transcription analysis
- ML heuristics (keyword detection, pattern matching)
- Manual annotations
"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.telemetry.metrics import MetricsCollector
from src.telemetry.events import EventLogger

logger = logging.getLogger(__name__)


class DetectionMethod(Enum):
    """Ad detection methods"""
    TRANSCRIPTION = "transcription"
    ML_HEURISTIC = "ml_heuristic"
    MANUAL = "manual"
    HYBRID = "hybrid"


class AdType(Enum):
    """Types of advertisements"""
    PRE_ROLL = "pre_roll"
    MID_ROLL = "mid_roll"
    POST_ROLL = "post_roll"
    SPONSORED_SEGMENT = "sponsored_segment"
    HOST_READ = "host_read"


@dataclass
class AdSlot:
    """Detected ad slot"""
    start_time_seconds: float
    end_time_seconds: float
    duration_seconds: float
    ad_type: AdType
    detection_method: DetectionMethod
    confidence: float  # 0.0-1.0
    campaign_id: Optional[str] = None
    sponsor_name: Optional[str] = None
    transcript_segment: Optional[str] = None
    keywords_detected: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriptSegment:
    """Transcript segment with timing"""
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str] = None
    confidence: float = 1.0


class AdDetectionEngine:
    """
    Ad Slot Detection Engine
    
    Uses multiple methods to detect ad slots:
    1. Transcription analysis (keyword detection, pattern matching)
    2. ML heuristics (temporal patterns, speaker changes)
    3. Manual annotations (user-provided)
    """
    
    # Common ad-related keywords
    AD_KEYWORDS = [
        "sponsor", "sponsored", "advertisement", "ad", "commercial",
        "promo code", "promo", "discount", "coupon", "offer",
        "visit", "go to", "check out", "try", "sign up",
        "use code", "code", "save", "deal", "special offer"
    ]
    
    # Transition phrases that often precede ads
    TRANSITION_PHRASES = [
        "we'll be right back", "after this", "before we continue",
        "let's take a break", "we'll return", "stay tuned",
        "coming up", "but first", "now a word from"
    ]
    
    def __init__(
        self,
        metrics_collector: MetricsCollector,
        event_logger: EventLogger
    ):
        self.metrics = metrics_collector
        self.events = event_logger
        
    async def detect_ads_from_transcript(
        self,
        episode_id: str,
        transcript_segments: List[TranscriptSegment],
        episode_duration_seconds: float
    ) -> List[AdSlot]:
        """
        Detect ad slots from transcript segments
        
        Args:
            episode_id: Episode identifier
            transcript_segments: List of transcript segments with timing
            episode_duration_seconds: Total episode duration
            
        Returns:
            List of detected ad slots
        """
        ad_slots = []
        
        # Method 1: Keyword-based detection
        keyword_slots = await self._detect_by_keywords(transcript_segments)
        ad_slots.extend(keyword_slots)
        
        # Method 2: Pattern-based detection (transition phrases)
        pattern_slots = await self._detect_by_patterns(transcript_segments, episode_duration_seconds)
        ad_slots.extend(pattern_slots)
        
        # Method 3: Temporal pattern detection
        temporal_slots = await self._detect_temporal_patterns(transcript_segments, episode_duration_seconds)
        ad_slots.extend(temporal_slots)
        
        # Merge overlapping slots
        merged_slots = self._merge_overlapping_slots(ad_slots)
        
        # Calculate confidence scores
        scored_slots = [self._calculate_confidence(slot, transcript_segments) for slot in merged_slots]
        
        # Record telemetry
        self.metrics.increment_counter(
            "ad_slots_detected",
            tags={
                "episode_id": episode_id,
                "method": DetectionMethod.TRANSCRIPTION.value,
                "count": len(scored_slots)
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="ad_detection_completed",
            user_id=None,
            properties={
                "episode_id": episode_id,
                "method": DetectionMethod.TRANSCRIPTION.value,
                "slots_detected": len(scored_slots),
                "total_duration_seconds": sum(s.duration_seconds for s in scored_slots)
            }
        )
        
        return scored_slots
    
    async def _detect_by_keywords(
        self,
        segments: List[TranscriptSegment]
    ) -> List[AdSlot]:
        """Detect ads by keyword matching"""
        ad_slots = []
        
        for segment in segments:
            text_lower = segment.text.lower()
            
            # Count keyword matches
            keyword_matches = [kw for kw in self.AD_KEYWORDS if kw in text_lower]
            
            if len(keyword_matches) >= 2:  # At least 2 keywords
                # Determine ad type based on position
                ad_type = self._classify_ad_type(segment.start_time, segment.end_time)
                
                slot = AdSlot(
                    start_time_seconds=segment.start_time,
                    end_time_seconds=segment.end_time,
                    duration_seconds=segment.end_time - segment.start_time,
                    ad_type=ad_type,
                    detection_method=DetectionMethod.ML_HEURISTIC,
                    confidence=min(0.7, 0.3 + len(keyword_matches) * 0.1),
                    transcript_segment=segment.text,
                    keywords_detected=keyword_matches
                )
                ad_slots.append(slot)
        
        return ad_slots
    
    async def _detect_by_patterns(
        self,
        segments: List[TranscriptSegment],
        episode_duration: float
    ) -> List[AdSlot]:
        """Detect ads by transition phrase patterns"""
        ad_slots = []
        
        for i, segment in enumerate(segments):
            text_lower = segment.text.lower()
            
            # Check for transition phrases
            for phrase in self.TRANSITION_PHRASES:
                if phrase in text_lower:
                    # Look ahead for potential ad content
                    if i + 1 < len(segments):
                        next_segment = segments[i + 1]
                        
                        # Check if next segment contains ad keywords
                        next_text_lower = next_segment.text.lower()
                        keyword_count = sum(1 for kw in self.AD_KEYWORDS if kw in next_text_lower)
                        
                        if keyword_count >= 1:
                            # Create slot spanning transition + ad content
                            ad_type = self._classify_ad_type(segment.start_time, next_segment.end_time)
                            
                            slot = AdSlot(
                                start_time_seconds=segment.start_time,
                                end_time_seconds=next_segment.end_time,
                                duration_seconds=next_segment.end_time - segment.start_time,
                                ad_type=ad_type,
                                detection_method=DetectionMethod.ML_HEURISTIC,
                                confidence=0.75,
                                transcript_segment=f"{segment.text} {next_segment.text}",
                                keywords_detected=[phrase]
                            )
                            ad_slots.append(slot)
        
        return ad_slots
    
    async def _detect_temporal_patterns(
        self,
        segments: List[TranscriptSegment],
        episode_duration: float
    ) -> List[AdSlot]:
        """Detect ads based on temporal patterns (e.g., regular intervals)"""
        ad_slots = []
        
        # Common ad placement patterns:
        # - Pre-roll: First 5% of episode
        # - Mid-roll: 25%, 50%, 75% marks
        # - Post-roll: Last 5% of episode
        
        check_points = [
            (0.0, 0.05, AdType.PRE_ROLL),  # First 5%
            (0.25, 0.30, AdType.MID_ROLL),  # ~25% mark
            (0.50, 0.55, AdType.MID_ROLL),  # ~50% mark
            (0.75, 0.80, AdType.MID_ROLL),  # ~75% mark
            (0.95, 1.0, AdType.POST_ROLL),  # Last 5%
        ]
        
        for start_ratio, end_ratio, ad_type in check_points:
            start_time = episode_duration * start_ratio
            end_time = episode_duration * end_ratio
            
            # Find segments in this time range
            matching_segments = [
                s for s in segments
                if start_time <= s.start_time <= end_time or start_time <= s.end_time <= end_time
            ]
            
            if matching_segments:
                # Check if segments contain ad-like content
                combined_text = " ".join(s.text.lower() for s in matching_segments)
                keyword_count = sum(1 for kw in self.AD_KEYWORDS if kw in combined_text)
                
                if keyword_count >= 1:
                    actual_start = min(s.start_time for s in matching_segments)
                    actual_end = max(s.end_time for s in matching_segments)
                    
                    slot = AdSlot(
                        start_time_seconds=actual_start,
                        end_time_seconds=actual_end,
                        duration_seconds=actual_end - actual_start,
                        ad_type=ad_type,
                        detection_method=DetectionMethod.ML_HEURISTIC,
                        confidence=0.6,  # Lower confidence for temporal-only detection
                        transcript_segment=" ".join(s.text for s in matching_segments),
                        keywords_detected=[kw for kw in self.AD_KEYWORDS if kw in combined_text]
                    )
                    ad_slots.append(slot)
        
        return ad_slots
    
    def _classify_ad_type(
        self,
        start_time: float,
        end_time: float,
        episode_duration: Optional[float] = None
    ) -> AdType:
        """Classify ad type based on position"""
        if episode_duration:
            position_ratio = start_time / episode_duration
            
            if position_ratio < 0.1:
                return AdType.PRE_ROLL
            elif position_ratio > 0.9:
                return AdType.POST_ROLL
            else:
                return AdType.MID_ROLL
        else:
            # Default to mid-roll if duration unknown
            return AdType.MID_ROLL
    
    def _calculate_confidence(
        self,
        slot: AdSlot,
        segments: List[TranscriptSegment]
    ) -> AdSlot:
        """Calculate confidence score for ad slot"""
        confidence_factors = []
        
        # Factor 1: Keyword density
        if slot.keywords_detected:
            keyword_density = len(slot.keywords_detected) / max(1, len(slot.transcript_segment.split()) if slot.transcript_segment else 1)
            confidence_factors.append(min(0.3, keyword_density * 0.3))
        
        # Factor 2: Duration (ads are typically 30-180 seconds)
        if 30 <= slot.duration_seconds <= 180:
            confidence_factors.append(0.2)
        elif 15 <= slot.duration_seconds < 30 or 180 < slot.duration_seconds <= 300:
            confidence_factors.append(0.1)
        
        # Factor 3: Detection method
        if slot.detection_method == DetectionMethod.MANUAL:
            confidence_factors.append(0.3)  # Manual annotations are high confidence
        elif slot.detection_method == DetectionMethod.TRANSCRIPTION:
            confidence_factors.append(0.2)
        elif slot.detection_method == DetectionMethod.ML_HEURISTIC:
            confidence_factors.append(0.1)
        
        # Factor 4: Pattern matching (transition phrases)
        if slot.transcript_segment:
            text_lower = slot.transcript_segment.lower()
            transition_match = any(phrase in text_lower for phrase in self.TRANSITION_PHRASES)
            if transition_match:
                confidence_factors.append(0.2)
        
        # Calculate final confidence (capped at 1.0)
        final_confidence = min(1.0, slot.confidence + sum(confidence_factors))
        
        slot.confidence = final_confidence
        return slot
    
    def _merge_overlapping_slots(self, slots: List[AdSlot]) -> List[AdSlot]:
        """Merge overlapping ad slots"""
        if not slots:
            return []
        
        # Sort by start time
        sorted_slots = sorted(slots, key=lambda s: s.start_time_seconds)
        merged = [sorted_slots[0]]
        
        for current in sorted_slots[1:]:
            last = merged[-1]
            
            # Check if overlapping
            if current.start_time_seconds <= last.end_time_seconds:
                # Merge slots
                merged[-1] = AdSlot(
                    start_time_seconds=min(last.start_time_seconds, current.start_time_seconds),
                    end_time_seconds=max(last.end_time_seconds, current.end_time_seconds),
                    duration_seconds=max(last.end_time_seconds, current.end_time_seconds) - min(last.start_time_seconds, current.start_time_seconds),
                    ad_type=last.ad_type,  # Keep first ad type
                    detection_method=DetectionMethod.HYBRID if last.detection_method != current.detection_method else last.detection_method,
                    confidence=max(last.confidence, current.confidence),
                    campaign_id=last.campaign_id or current.campaign_id,
                    sponsor_name=last.sponsor_name or current.sponsor_name,
                    transcript_segment=f"{last.transcript_segment or ''} {current.transcript_segment or ''}".strip(),
                    keywords_detected=list(set((last.keywords_detected or []) + (current.keywords_detected or [])))
                )
            else:
                merged.append(current)
        
        return merged
    
    async def detect_ads_ml_heuristic(
        self,
        episode_id: str,
        audio_features: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[AdSlot]:
        """
        Detect ads using ML heuristics (audio features, metadata)
        
        Args:
            episode_id: Episode identifier
            audio_features: Audio analysis features (volume changes, silence, etc.)
            metadata: Episode metadata
            
        Returns:
            List of detected ad slots
        """
        # Placeholder for ML-based detection
        # In production, this would use:
        # - Audio volume analysis (ads often have different volume)
        # - Silence detection (pauses before/after ads)
        # - Speaker change detection
        # - Music/sound effect detection
        
        ad_slots = []
        
        if audio_features:
            # Example: Detect volume changes that might indicate ads
            volume_changes = audio_features.get("volume_changes", [])
            for change in volume_changes:
                if change.get("magnitude", 0) > 0.3:  # Significant volume change
                    slot = AdSlot(
                        start_time_seconds=change.get("start_time", 0),
                        end_time_seconds=change.get("end_time", 0),
                        duration_seconds=change.get("duration", 0),
                        ad_type=AdType.MID_ROLL,
                        detection_method=DetectionMethod.ML_HEURISTIC,
                        confidence=0.5,
                        metadata={"feature": "volume_change"}
                    )
                    ad_slots.append(slot)
        
        # Record telemetry
        self.metrics.increment_counter(
            "ad_slots_detected",
            tags={
                "episode_id": episode_id,
                "method": DetectionMethod.ML_HEURISTIC.value,
                "count": len(ad_slots)
            }
        )
        
        return ad_slots
    
    async def add_manual_annotation(
        self,
        episode_id: str,
        start_time_seconds: float,
        end_time_seconds: float,
        campaign_id: Optional[str] = None,
        sponsor_name: Optional[str] = None
    ) -> AdSlot:
        """
        Add manual ad annotation
        
        Args:
            episode_id: Episode identifier
            start_time_seconds: Start time of ad
            end_time_seconds: End time of ad
            campaign_id: Optional campaign ID
            sponsor_name: Optional sponsor name
            
        Returns:
            Created ad slot
        """
        slot = AdSlot(
            start_time_seconds=start_time_seconds,
            end_time_seconds=end_time_seconds,
            duration_seconds=end_time_seconds - start_time_seconds,
            ad_type=AdType.MID_ROLL,  # Default, can be updated
            detection_method=DetectionMethod.MANUAL,
            confidence=1.0,  # Manual annotations are 100% confident
            campaign_id=campaign_id,
            sponsor_name=sponsor_name
        )
        
        # Record telemetry
        self.metrics.increment_counter(
            "ad_slots_detected",
            tags={
                "episode_id": episode_id,
                "method": DetectionMethod.MANUAL.value,
                "count": 1
            }
        )
        
        # Log event
        await self.events.log_event(
            event_type="ad_slot_annotated",
            user_id=None,
            properties={
                "episode_id": episode_id,
                "start_time_seconds": start_time_seconds,
                "end_time_seconds": end_time_seconds,
                "campaign_id": campaign_id,
                "sponsor_name": sponsor_name
            }
        )
        
        return slot
