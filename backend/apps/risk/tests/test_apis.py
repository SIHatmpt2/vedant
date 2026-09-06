"""API contract tests for risk geospatial endpoints."""
from django.contrib.gis.geos import Polygon
from django.test import TestCase
from django.utils import timezone
from apps.risk.models import HistoricalFloodEvent
from apps.risk.services.zone_manager import ZoneManager
class RiskApiTests(TestCase):
    def setUp(self):
        shape=Polygon(((77,20),(77.01,20),(77.01,20.01),(77,20.01),(77,20))); self.zone=ZoneManager().create_zone(name="Test", geometry=shape, flood_prone=True, risk_priority=90)
    def test_nearby_and_high_risk(self):
        self.assertEqual(self.client.get("/api/risk/zones/nearby/?lat=20&lon=77&radius=5").status_code,200); self.assertEqual(self.client.get("/api/risk/high-risk/").status_code,200)
    def test_history_filters_and_validates(self):
        response=self.client.get("/api/risk/history/?zone=%s" % self.zone.pk); self.assertEqual(response.status_code,200); self.assertEqual(self.client.get("/api/risk/history/?start=no").status_code,400)
