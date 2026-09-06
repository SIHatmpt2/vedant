"""Persistence models only; spatial computation belongs in services/selectors."""
from django.contrib.gis.db import models
from django.db import models as db_models


class RiskZone(models.Model):
    """An operator-managed flood-risk polygon stored in WGS84 PostGIS."""
    name = db_models.CharField(max_length=160)
    state = db_models.CharField(max_length=80, blank=True, db_index=True)
    geometry = models.PolygonField(srid=4326, spatial_index=True)
    centroid = models.PointField(srid=4326, spatial_index=True, null=True, blank=True)
    area = db_models.FloatField(default=0, help_text="Area in square metres.")
    risk_priority = db_models.PositiveSmallIntegerField(default=0, db_index=True)
    flood_prone = db_models.BooleanField(default=False, db_index=True)
    active = db_models.BooleanField(default=True, db_index=True)
    population = db_models.PositiveIntegerField(default=0)
    metadata = db_models.JSONField(default=dict, blank=True)
    created_at = db_models.DateTimeField(auto_now_add=True)
    updated_at = db_models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [db_models.Index(fields=["active", "risk_priority"])]
        ordering = ["-risk_priority", "name"]


class HistoricalFloodEvent(models.Model):
    """A normalized historical flood record with a spatial event location."""
    occurred_at = db_models.DateTimeField(db_index=True)
    location = models.PointField(srid=4326, spatial_index=True)
    severity = db_models.PositiveSmallIntegerField(help_text="Normalized severity from 1 to 100.")
    state = db_models.CharField(max_length=80, blank=True, db_index=True)
    source = db_models.CharField(max_length=120)
    metadata = db_models.JSONField(default=dict, blank=True)
    external_id = db_models.CharField(max_length=160, unique=True)
    created_at = db_models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [db_models.Index(fields=["state", "occurred_at"])]
        ordering = ["-occurred_at"]


class RiskAssessment(models.Model):
    """Latest calculated risk evidence for a zone; one row per zone and instant."""
    zone = db_models.ForeignKey(RiskZone, on_delete=db_models.CASCADE, related_name="assessments")
    score = db_models.PositiveSmallIntegerField()
    level = db_models.CharField(max_length=20)
    confidence = db_models.FloatField()
    breakdown = db_models.JSONField(default=dict)
    assessed_at = db_models.DateTimeField(db_index=True)

    class Meta:
        constraints = [db_models.UniqueConstraint(fields=["zone", "assessed_at"], name="unique_zone_assessment_time")]
        indexes = [db_models.Index(fields=["zone", "-assessed_at"])]
        ordering = ["-assessed_at"]
