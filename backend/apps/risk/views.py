"""Thin DRF transport views; selectors/services own all data and calculation work."""
from datetime import datetime
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from . import selectors
from .constants import DEFAULT_RADIUS_KM, MAX_RADIUS_KM
from .models import RiskZone
from .services.cache import coordinate_key, get_or_set


def error(code: str, status: int = 400) -> JsonResponse:
    """Return the API's stable, compact validation error format."""
    return JsonResponse({"error": code}, status=status)


def coordinates(request: View) -> tuple[float, float] | None:
    """Parse bounded WGS84 coordinate query parameters."""
    try:
        latitude, longitude = float(request.GET["lat"]), float(request.GET["lon"])
    except (KeyError, ValueError): return None
    return (latitude, longitude) if -90 <= latitude <= 90 and -180 <= longitude <= 180 else None


def zone_data(zone: RiskZone, include_distance: bool = False) -> dict:
    """Serialize safe zone projection without putting business logic in serializers."""
    payload = {"id": zone.id, "name": zone.name, "priority": zone.risk_priority, "flood_prone": zone.flood_prone}
    if include_distance: payload["distance_km"] = round(zone.distance.km, 3)
    return payload


class NearbyZonesView(View):
    """Return cached active zones within a validated geographic radius."""
    def get(self, request):
        point = coordinates(request)
        if not point: return error("invalid_coordinates")
        try: radius = float(request.GET.get("radius", DEFAULT_RADIUS_KM))
        except ValueError: return error("invalid_radius")
        if radius <= 0 or radius > MAX_RADIUS_KM: return error("invalid_radius")
        latitude, longitude = point
        payload = get_or_set(coordinate_key("zones", latitude, longitude, radius), lambda: [zone_data(zone, True) for zone in selectors.zones_within_radius(latitude, longitude, radius)])
        return JsonResponse({"zones": payload, "radius_km": radius})


class HighRiskZonesView(View):
    """Return active severe/flood-prone zones."""
    def get(self, request):
        return JsonResponse({"zones": [zone_data(zone) for zone in selectors.high_risk_zones()]})


class HistoricalEventsView(View):
    """Provide a paginated, filterable historical flood evidence feed."""
    def get(self, request):
        zone_id = request.GET.get("zone")
        try: zone_id = int(zone_id) if zone_id else None
        except ValueError: return error("invalid_zone")
        if zone_id and not RiskZone.objects.filter(pk=zone_id).exists(): return error("zone_not_found", 404)
        try:
            start = datetime.fromisoformat(request.GET["start"]) if request.GET.get("start") else None
            end = datetime.fromisoformat(request.GET["end"]) if request.GET.get("end") else None
        except ValueError: return error("invalid_date")
        if start and end and start > end: return error("invalid_date_range")
        try: page = max(1, int(request.GET.get("page", 1)))
        except ValueError: return error("invalid_page")
        events = selectors.historical_events_filtered(zone_id, request.GET.get("state", ""), start, end)
        result = Paginator(events, 25).get_page(page)
        return JsonResponse({"count": result.paginator.count, "page": result.number, "results": [{"id": e.id, "occurred_at": e.occurred_at.isoformat(), "severity": e.severity, "state": e.state, "source": e.source} for e in result]})


class ZoneDetailView(View):
    """Return geometry summary, latest assessment and in-zone historical evidence."""
    def get(self, request, zone_id: int):
        zone = get_object_or_404(RiskZone.objects.prefetch_related("assessments"), pk=zone_id)
        assessment = zone.assessments.first()
        events = selectors.historical_events_filtered(zone.id, "", None, None)[:25]
        return JsonResponse({"id": zone.id, "name": zone.name, "population": zone.population, "geometry": {"type": zone.geometry.geom_type, "area_sqm": zone.area, "centroid": [zone.centroid.y, zone.centroid.x]}, "latest_assessment": None if not assessment else {"score": assessment.score, "level": assessment.level, "confidence": assessment.confidence, "breakdown": assessment.breakdown, "timestamp": assessment.assessed_at.isoformat()}, "historical_events": [{"id": e.id, "severity": e.severity, "occurred_at": e.occurred_at.isoformat()} for e in events]})
