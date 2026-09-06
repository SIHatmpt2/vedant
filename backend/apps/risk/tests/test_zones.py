"""Transactional tests for zone write service."""
from django.contrib.gis.geos import Polygon
from django.test import TestCase
from apps.risk.services.zone_manager import ZoneManager

def square(x=77, y=20): return Polygon(((x,y),(x+.01,y),(x+.01,y+.01),(x,y+.01),(x,y)))
class ZoneManagerTests(TestCase):
    def test_create_derives_centroid_and_metric_area(self):
        zone=ZoneManager().create_zone(name="A", geometry=square()); self.assertIsNotNone(zone.centroid); self.assertGreater(zone.area, 0)
    def test_update_refreshes_geometry_properties(self):
        manager=ZoneManager(); zone=manager.create_zone(name="A", geometry=square()); manager.update_zone(zone, geometry=square(78,21)); zone.refresh_from_db(); self.assertAlmostEqual(zone.centroid.x, 78.005, 3)
    def test_merge_deactivates_overlap(self):
        manager=ZoneManager(); one=manager.create_zone(name="A", geometry=square()); two=manager.create_zone(name="B", geometry=square(77.005,20.005)); manager.merge_overlapping(one); two.refresh_from_db(); self.assertFalse(two.active)
