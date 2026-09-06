"""Read-only PostGIS query functions for risk services and API views."""
from datetime import datetime
from typing import Optional
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import QuerySet
from django.utils import timezone
from .models import HistoricalFloodEvent, RiskAssessment, RiskZone


def _point(latitude: float, longitude: float) -> Point:
    return Point(longitude, latitude, srid=4326)


def zone_by_coordinates(latitude: float, longitude: float) -> Optional[RiskZone]:
    """Return the active zone containing a coordinate, if any."""
    return RiskZone.objects.filter(active=True, geometry__covers=_point(latitude, longitude)).first()


def nearest_zone(latitude: float, longitude: float) -> Optional[RiskZone]:
    """Return nearest active zone annotated with geographic distance."""
    point = _point(latitude, longitude)
    return RiskZone.objects.filter(active=True).annotate(distance=Distance("centroid", point)).order_by("distance").first()


def zones_within_radius(latitude: float, longitude: float, radius_km: float) -> QuerySet[RiskZone]:
    """Return active zones within radius, closest first, in one spatial query."""
    point = _point(latitude, longitude)
    return RiskZone.objects.filter(active=True, centroid__distance_lte=(point, D(km=radius_km))).annotate(distance=Distance("centroid", point)).order_by("distance")


def high_risk_zones() -> QuerySet[RiskZone]:
    """Return active severe/flood-prone zones with assessment relationships prefetched."""
    return RiskZone.objects.filter(active=True, flood_prone=True, risk_priority__gte=75).prefetch_related("assessments").order_by("-risk_priority")


def recent_assessments(limit: int = 100) -> QuerySet[RiskAssessment]:
    """Fetch recent assessments with zones, avoiding per-record zone reads."""
    return RiskAssessment.objects.select_related("zone").order_by("-assessed_at")[:limit]


def historical_events_nearby(latitude: float, longitude: float, radius_km: float = 25) -> QuerySet[HistoricalFloodEvent]:
    """Return flood events in a radius with distance annotation."""
    point = _point(latitude, longitude)
    return HistoricalFloodEvent.objects.filter(location__distance_lte=(point, D(km=radius_km))).annotate(distance=Distance("location", point)).order_by("-occurred_at")


def flood_prone_zones() -> QuerySet[RiskZone]:
    """Return all active zones explicitly identified as flood prone."""
    return RiskZone.objects.filter(active=True, flood_prone=True).order_by("-risk_priority")


def historical_events_filtered(zone_id: Optional[int], state: str, start: Optional[datetime], end: Optional[datetime]) -> QuerySet[HistoricalFloodEvent]:
    """Build a filterable historical event query used by the paginated endpoint."""
    events = HistoricalFloodEvent.objects.all()
    if zone_id:
        zone = RiskZone.objects.get(pk=zone_id)
        events = events.filter(location__within=zone.geometry)
    if state:
        events = events.filter(state__iexact=state)
    if start:
        events = events.filter(occurred_at__gte=start)
    if end:
        events = events.filter(occurred_at__lte=end)
    return events
