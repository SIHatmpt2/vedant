"""Unit tests for terrain normalization."""
from django.test import SimpleTestCase
from apps.risk.services.terrain import TerrainService

class TerrainServiceTests(SimpleTestCase):
    def test_score_rewards_low_elevation_flat_high_drainage_land(self):
        result = TerrainService().score(20, 77, {"elevation": 310, "slope": 12.5, "drainage_density": 80})
        self.assertEqual(result["elevation"], 310.0); self.assertEqual(result["slope"], 12.5); self.assertGreater(result["terrain_score"], 0)
    def test_missing_terrain_is_explicit(self): self.assertIsNone(TerrainService().score(20, 77)["terrain_score"])
