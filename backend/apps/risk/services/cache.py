"""Small cache boundary for expensive geospatial intelligence queries."""
import logging
from typing import Any, Callable
from django.core.cache import cache
from ..constants import CACHE_TTL_SECONDS
logger = logging.getLogger(__name__)


def coordinate_key(prefix: str, latitude: float, longitude: float, radius: float | None = None) -> str:
    """Create stable cache keys that avoid insignificant floating point variation."""
    pieces = [prefix, f"{latitude:.5f}", f"{longitude:.5f}"]
    if radius is not None: pieces.append(f"{radius:.2f}")
    return ":".join(pieces)


def get_or_set(key: str, factory: Callable[[], Any]) -> Any:
    """Read or populate a 15-minute cached value and emit structured cache diagnostics."""
    value = cache.get(key)
    if value is not None:
        logger.info("risk_cache_hit", extra={"cache_key": key})
        return value
    logger.info("risk_cache_miss", extra={"cache_key": key})
    value = factory()
    cache.set(key, value, CACHE_TTL_SECONDS)
    return value
