"""Risk application configuration."""
from django.apps import AppConfig


class RiskConfig(AppConfig):
    """Register risk tasks and PostGIS models."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.risk"
