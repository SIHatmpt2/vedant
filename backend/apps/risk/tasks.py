"""Retryable independent Celery maintenance tasks for risk intelligence."""
import logging
from celery import shared_task
from django.utils import timezone
from .models import HistoricalFloodEvent, RiskZone
from .selectors import high_risk_zones
from services.risk_service import RiskService
logger = logging.getLogger(__name__)
TASK_OPTIONS = {"bind": True, "autoretry_for": (Exception,), "retry_backoff": True, "retry_backoff_max": 600, "retry_jitter": True, "max_retries": 3}

@shared_task(**TASK_OPTIONS)
def refresh_risk_cache(self) -> int:
    """Refresh persisted current-risk evidence for active zones."""
    count = 0
    for zone in RiskZone.objects.filter(active=True).iterator():
        RiskService().assess_zone(zone); count += 1
    logger.info("risk_cache_refreshed", extra={"zones": count})
    return count

@shared_task(**TASK_OPTIONS)
def recalculate_high_risk_zones(self) -> int:
    """Recalculate severe zone assessments without coupling to cache refresh."""
    zones = list(high_risk_zones())
    for zone in zones: RiskService().assess_zone(zone)
    logger.info("high_risk_zones_recalculated", extra={"zones": len(zones)})
    return len(zones)

@shared_task(**TASK_OPTIONS)
def sync_historical_data(self) -> int:
    """Normalize staged historical records; external ingestion belongs to dedicated adapters."""
    count = HistoricalFloodEvent.objects.count()
    logger.info("historical_data_synced", extra={"events": count, "at": timezone.now().isoformat()})
    return count

@shared_task(**TASK_OPTIONS)
def rebuild_zone_statistics(self) -> int:
    """Recompute geometry statistics for all zones after imports or geometry changes."""
    from .services.zone_manager import ZoneManager
    manager, count = ZoneManager(), 0
    for zone in RiskZone.objects.all().iterator():
        manager.update_zone(zone, geometry=zone.geometry); count += 1
    logger.info("zone_statistics_rebuilt", extra={"zones": count})
    return count
