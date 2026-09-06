"""Shared, documented policy values for flood-risk intelligence."""
from datetime import timedelta

CACHE_TTL_SECONDS = 15 * 60
DEFAULT_RADIUS_KM = 10.0
MAX_RADIUS_KM = 100.0
EARTH_SRID = 4326
METER_SRID = 3857
HIGH_RISK_PRIORITY = 75
SEVERE_SCORE = 80
ASSESSMENT_FRESHNESS = timedelta(minutes=15)
RISK_WEIGHTS = {"rainfall": 0.35, "river": 0.30, "terrain": 0.20, "historical": 0.15}
UNCERTAINTY_BY_SIGNALS = {4: "low", 3: "moderate", 2: "high", 1: "critical", 0: "critical"}
