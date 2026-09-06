"""Celery task tests run tasks eagerly without a worker or network."""
from unittest.mock import patch
from django.test import TestCase
from apps.risk.tasks import sync_historical_data
class TaskTests(TestCase):
    def test_historical_sync_executes(self): self.assertEqual(sync_historical_data.apply().result, 0)
    @patch("apps.risk.tasks.HistoricalFloodEvent.objects.count", side_effect=RuntimeError("temporary"))
    def test_task_declares_autoretry_policy(self, mocked): self.assertTrue(sync_historical_data.autoretry_for)
