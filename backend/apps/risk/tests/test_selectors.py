"""PostGIS selector tests."""
from django.contrib.gis.geos import Polygon
from django.test import TestCase
from apps.risk.selectors import nearest_zone, zones_within_radius
from apps.risk.services.zone_manager import ZoneManager

def square(x,y): return Polygon(((x,y),(x+.01,y),(x+.01,y+.01),(x,y+.01),(x,y)))
class SelectorTests(TestCase):
    def setUp(self):
        self.near=ZoneManager().create_zone(name="near", geometry=square(77,20)); ZoneManager().create_zone(name="far", geometry=square(78,21))
    def test_nearest_zone_uses_centroid_distance(self): self.assertEqual(nearest_zone(20,77).pk, self.near.pk)
    def test_radius_limits_postgis_results(self): self.assertEqual(zones_within_radius(20,77,5).count(), 1)
