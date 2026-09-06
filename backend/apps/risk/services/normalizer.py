"""Normalization functions that isolate source-specific values from risk calculations."""
from typing import Any


def score(value: Any, maximum: float = 100) -> float | None:
    """Coerce a source signal to a safe 0--100 range, retaining missing evidence."""
    if value is None: return None
    return round(max(0.0, min(100.0, float(value) / maximum * 100)), 2)


def weather(payload: dict[str, Any]) -> float | None:
    """Normalize weather module rainfall score."""
    return score(payload.get("rainfall_score", payload.get("rainfall")))


def river(payload: dict[str, Any]) -> float | None:
    """Normalize river module overflow score."""
    return score(payload.get("river_score", payload.get("overflow_score")))
