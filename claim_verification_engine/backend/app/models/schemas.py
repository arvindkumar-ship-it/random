from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from enum import Enum


class VerdictType(str, Enum):
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    MIXED = "MIXED"
    UNVERIFIABLE = "UNVERIFIABLE"


class ClaimInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    image_path: Optional[str] = None
    claimed_location: Optional[str] = None
    claimed_timestamp: Optional[datetime] = None


class Evidence(BaseModel):
    source_url: str
    source_domain: str
    snippet: str
    publication_date: Optional[datetime] = None
    supports_claim: bool
    credibility_score: float = Field(ge=0.0, le=1.0)
    recency_score: float = Field(ge=0.0, le=1.0)
    relevance_score: float = Field(ge=0.0, le=1.0)
    entity_overlap: float = Field(ge=0.0, le=1.0)
    temporal_verified: Optional[bool] = None
    geolocation_verified: Optional[bool] = None


class VerificationResult(BaseModel):
    claim: str
    verdict: VerdictType
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_interval: Tuple[float, float]
    reasoning: str
    evidence_count: int
    supporting_count: int
    contradicting_count: int
    evidence_list: List[Evidence]
    method_scores: Dict[str, float]
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)
