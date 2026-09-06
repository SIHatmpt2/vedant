"""Database tests for historical spatial evidence weighting."""
from datetime import timedelta
from django.contrib.gis.geos import Point
from django.test import TestCase
from django.utils import timezone
from apps.risk.models import HistoricalFloodEvent
from apps.risk.services.historical import HistoricalService

class HistoricalServiceTests(TestCase):
    def test_near_recent_severe_event_outweighs_distant_old_event(self):
        now = timezone.now()
        HistoricalFloodEvent.objects.create(external_id="near", location=Point(77, 20), severity=100, occurred_at=now, source="test")
        HistoricalFloodEvent.objects.create(external_id="far", location=Point(77.2, 20.2), severity=100, occurred_at=now-timedelta(days=3000), source="test")
        result = HistoricalService().score(20, 77, 50)
        self.assertEqual(result["events"], 2); self.assertGreater(result["historical_score"], 30)
