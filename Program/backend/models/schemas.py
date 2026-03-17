from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class RiskCategory(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    unknown = "Unknown"


class RiskIndicator(BaseModel):
    category: RiskCategory
    numeric: int = Field(ge=1, le=3)
    source: str  # 'realtime' or 'fallback'
    is_fallback: bool = False
    timestamp: Optional[str] = None  # ISO8601


class SegmentAssessment(BaseModel):
    mode: str
    from_name: str
    to_name: str
    crowding: RiskIndicator
    delay: RiskIndicator


class RouteStep(BaseModel):
    """One leg of a route: a walk, a bus ride, a train ride, or a drive."""
    mode: str  # "Walk", "Bus", "Train", "Drive"
    from_name: str
    to_name: str
    duration_min: float
    distance_m: Optional[float] = None
    # Transit-specific
    line_name: Optional[str] = None
    num_stops: Optional[int] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    headsign: Optional[str] = None
    # Per-step risk (None for walking steps)
    crowding: Optional[RiskIndicator] = None
    delay: Optional[RiskIndicator] = None


class TripRequest(BaseModel):
    origin: str
    destination: str
    departure_time: Optional[str] = None
    # mode flags
    mrt_only: bool = False
    public_only: bool = False
    taxi: bool = True
    drive: bool = False
    hybrid_taxi: bool = False
    # constraints
    max_walk_min: Optional[int] = None
    max_transfers: Optional[int] = None
    max_budget: Optional[float] = None
    # weights (new 4-dimension model)
    wt_time: float = 0.25
    wt_cost: float = 0.25
    wt_risk: float = 0.25
    wt_comfort: float = 0.25


class RouteOption(BaseModel):
    category: str
    path_summary: str
    time_min: float
    cost_est: float
    cost_breakdown: Optional[Dict] = None
    distance_km: float = 0.0
    walk_min: float = 0.0
    transfers: int
    steps: List[RouteStep] = []
    overview_polyline: Optional[str] = None
    # Per-dimension raw risk values (kept for display)
    risk_crowding_cat: RiskCategory
    risk_crowding_num: int
    risk_delay_cat: RiskCategory
    risk_delay_num: int
    # Combined metrics
    risk_num: float = 0.0
    risk_cat: str = "Unknown"
    comfort_num: float = 0.0
    # Normalized scores (new 4-dimension model)
    normalized_time: float = 0.0
    normalized_cost: float = 0.0
    normalized_risk: float = 0.0
    normalized_comfort: float = 0.0
    score: float = 0.0
    uses_fallback: bool = False
    explanation: str = ""


class AssessmentResponse(BaseModel):
    trip: TripRequest
    segments: List[SegmentAssessment]
    message: Optional[str] = None


class AssessmentInput(BaseModel):
    route: dict


class RoutesResponse(BaseModel):
    trip: TripRequest
    routes: List[RouteOption]
    message: Optional[str] = None


class DatasetStatus(BaseModel):
    last_retrieved: Optional[str] = None
    ttl_sec: int
    is_fallback: bool = False
    source: str = "realtime"


class DatasetsStatusResponse(BaseModel):
    sources: Dict[str, DatasetStatus]


class Settings(BaseModel):
    language: str = "en"
    units: str = "metric"
    default_wt_time: float = 0.25
    default_wt_cost: float = 0.25
    default_wt_risk: float = 0.25
    default_wt_comfort: float = 0.25
