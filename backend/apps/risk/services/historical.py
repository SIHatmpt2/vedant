"""Historical flood scoring with distance, severity and recency decay."""
from datetime import datetime
from math import exp
from typing import Any
from django.utils import timezone
from .. import selectors
from .cache import coordinate_key, get_or_set


class HistoricalService:
    """Turn nearby event evidence into a bounded, explainable historical risk signal."""
    def nearby(self, latitude: float, longitude: float, radius_km: float = 25) -> list[dict[str, Any]]:
        """Retrieve and cache compact nearby-event evidence instead of model objects."""
        key = coordinate_key("history", latitude, longitude, radius_km)
        def query() -> list[dict[str, Any]]:
            return [{"id": item.id, "severity": item.severity, "occurred_at": item.occurred_at.isoformat(), "distance_km": item.distance.km} for item in selectors.historical_events_nearby(latitude, longitude, radius_km)]
        return get_or_set(key, query)

    def score(self, latitude: float, longitude: float, radius_km: float = 25) -> dict[str, Any]:
        """Weight events exponentially by age and distance, linearly by severity."""
        events = self.nearby(latitude, longitude, radius_km)
        weighted = 0.0
        for event in events:
            occurred = datetime.fromisoformat(event["occurred_at"])
            age_days = max(0, (timezone.now() - occurred).total_seconds() / 86400)
            recency = exp(-age_days / 730.0)
            proximity = exp(-float(event["distance_km"]) / max(radius_km / 2, 1))
            weighted += (min(100, event["severity"]) / 100) * recency * proximity
        return {"historical_score": round(min(100, weighted * 35), 2), "events": len(events)}
