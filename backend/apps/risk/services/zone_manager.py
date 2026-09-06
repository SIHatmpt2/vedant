"""Transactional write service for PostGIS risk zones."""
import logging
from typing import Any
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.db.models.functions import Area, Centroid
from ..models import RiskZone
logger = logging.getLogger(__name__)


class ZoneManager:
    """Own zone creation, mutation, merge and geometry-derived properties."""
    def calculate_centroid(self, geometry: GEOSGeometry) -> GEOSGeometry:
        """Calculate centroid in geometry SRID."""
        return geometry.centroid

    def calculate_area(self, geometry: GEOSGeometry) -> float:
        """Calculate square-metre area using a metric projection."""
        metric = geometry.clone()
        metric.transform(3857)
        return round(metric.area, 2)

    @transaction.atomic
    def create_zone(self, *, name: str, geometry: GEOSGeometry, **fields: Any) -> RiskZone:
        """Persist an input polygon with service-generated centroid and area."""
        zone = RiskZone.objects.create(name=name, geometry=geometry, centroid=self.calculate_centroid(geometry), area=self.calculate_area(geometry), **fields)
        logger.info("risk_zone_created", extra={"zone_id": zone.pk, "name": name})
        return zone

    @transaction.atomic
    def update_zone(self, zone: RiskZone, **fields: Any) -> RiskZone:
        """Apply allowed attributes and refresh derived geometry values when changed."""
        geometry = fields.pop("geometry", None)
        if geometry is not None:
            zone.geometry, zone.centroid, zone.area = geometry, self.calculate_centroid(geometry), self.calculate_area(geometry)
        for field, value in fields.items():
            if field not in {"name", "state", "risk_priority", "flood_prone", "active", "population", "metadata"}:
                raise ValueError(f"Unsupported zone field: {field}")
            setattr(zone, field, value)
        zone.save()
        return zone

    @transaction.atomic
    def merge_overlapping(self, zone: RiskZone) -> RiskZone:
        """Union overlapping active zones into the supplied zone and deactivate inputs."""
        overlaps = RiskZone.objects.select_for_update().filter(active=True, geometry__overlaps=zone.geometry).exclude(pk=zone.pk)
        geometries = [zone.geometry, *[item.geometry for item in overlaps]]
        merged = geometries[0]
        for geometry in geometries[1:]: merged = merged.union(geometry)
        zone.geometry, zone.centroid, zone.area = merged, self.calculate_centroid(merged), self.calculate_area(merged)
        zone.risk_priority = max([zone.risk_priority, *[item.risk_priority for item in overlaps]])
        zone.flood_prone = zone.flood_prone or any(item.flood_prone for item in overlaps)
        zone.save()
        overlaps.update(active=False)
        logger.info("risk_zones_merged", extra={"zone_id": zone.pk, "merged_count": len(geometries) - 1})
        return zone

    def set_active(self, zone: RiskZone, active: bool) -> RiskZone:
        """Activate or deactivate a zone explicitly."""
        return self.update_zone(zone, active=active)
