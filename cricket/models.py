from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Listing:
    listing_id: Optional[str] = None
    source: str = ""
    source_url: str = ""
    dealer_name: str = ""
    dealer_type: str = ""
    location: str = ""
    distance_miles: Optional[float] = None
    year: Optional[int] = None
    make: str = ""
    model: str = ""
    trim: str = ""
    price: Optional[int] = None
    mileage: Optional[int] = None
    exterior_color: str = ""
    interior_color: str = ""
    color_score: str = "unknown"
    drivetrain: str = ""
    transmission: str = ""
    vin: str = ""
    stock_number: str = ""
    cpo: Optional[bool] = None
    accident_history: str = "unknown"
    owners: Optional[int] = None
    history_report_url: str = ""
    title_status: str = "unknown"
    service_records: str = ""
    rear_camera: str = "unknown"
    blind_spot_detection: str = "unknown"
    rear_cross_traffic_alert: str = "unknown"
    reverse_automatic_braking: str = "unknown"
    feature_confidence: str = "unknown"
    safety_evidence: Dict[str, str] = field(default_factory=dict)
    listing_age_days: Optional[int] = None
    first_seen_date: Optional[str] = None
    last_seen_date: Optional[str] = None
    price_change: Optional[int] = None
    notes: List[str] = field(default_factory=list)
    reject_reason: str = ""
    score: int = 0
    score_breakdown: Dict[str, Any] = field(default_factory=dict)
    price_confidence: str = "unknown"
    raw: Dict[str, Any] = field(default_factory=dict)

    def key(self) -> str:
        if self.vin:
            return "vin:%s" % self.vin.upper()
        if self.listing_id:
            return "%s:%s" % (self.source, self.listing_id)
        return "%s:%s:%s:%s:%s" % (
            self.source_url,
            self.year or "",
            self.mileage or "",
            self.price or "",
            self.dealer_name,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SourceResult:
    source_name: str
    raw_items: List[Dict[str, Any]] = field(default_factory=list)
    listings: List[Listing] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class RunResult:
    date: str
    listings: List[Listing]
    rejected: List[Listing]
    source_results: List[SourceResult]
    report_path: str
    raw_path: str
    normalized_path: str
    new_keys: List[str]
    removed_keys: List[str]
    price_changes: Dict[str, int]
    sync_paths: List[str] = field(default_factory=list)
    sync_errors: List[str] = field(default_factory=list)
