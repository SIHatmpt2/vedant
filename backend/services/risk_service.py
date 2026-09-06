"""Application facade joining normalized module signals, GIS and assessment persistence."""
from typing import Any
from django.utils import timezone
from apps.risk.models import RiskAssessment, RiskZone
from apps.risk.services.historical import HistoricalService
from apps.risk.services.risk_engine import RiskEngine
from apps.risk.services.terrain import TerrainService


class RiskService:
    """Orchestrate mandatory data modules through normalization into persisted risk evidence."""
    def assess_zone(self, zone: RiskZone, weather_score: float | None = None, river_score: float | None = None) -> dict[str, Any]:
        """Calculate an assessment and update the current time-bucketed assessment."""
        terrain = TerrainService().score(zone.centroid.y, zone.centroid.x, zone.metadata)
        history = HistoricalService().score(zone.centroid.y, zone.centroid.x)
        result = RiskEngine.calculate({"rainfall": weather_score, "river": river_score, "terrain": terrain["terrain_score"], "historical": history["historical_score"]})
        instant = timezone.now().replace(second=0, microsecond=0)
        RiskAssessment.objects.update_or_create(zone=zone, assessed_at=instant, defaults={"score": result["risk_score"], "level": result["risk_level"], "confidence": result["confidence"], "breakdown": result["breakdown"]})
        return result
